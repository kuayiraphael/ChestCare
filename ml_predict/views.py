from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from .models import PredictionResult
from .serializers import XrayPredictionSerializer, PredictionResultSerializer
from .utils import predictor
from dashboard.models import Patient
import logging
import numpy as np
import os
from django.conf import settings

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_chest_disease(request):
    """
    Predict chest disease from X-ray image with Grad-CAM visualization
    """
    prediction_result = None

    try:
        serializer = XrayPredictionSerializer(data=request.data)
        if serializer.is_valid():
            patient_id = serializer.validated_data['patient_id']
            xray_image = serializer.validated_data['xray_image']

            # Get patient
            patient = get_object_or_404(Patient, id=patient_id)

            # Create prediction result instance but don't save yet
            prediction_result = PredictionResult(
                patient=patient,
                xray_image=xray_image
            )

            # Save to get the file path (needed for prediction)
            prediction_result.save()

            # Make prediction
            try:
                logger.info(
                    f"Starting prediction for image: {prediction_result.xray_image.path}")

                # Check if predictor has loaded models
                if not predictor.models:
                    raise Exception(
                        "No ML models loaded. Please check model files and logs.")

                # Make the prediction
                prediction = predictor.predict(
                    prediction_result.xray_image.path)

                # Validation code (same as before)...
                if not prediction:
                    raise Exception("Prediction returned None or empty result")

                required_keys = ['predicted_disease',
                                 'confidence_score', 'all_predictions']
                missing_keys = [
                    key for key in required_keys if key not in prediction]
                if missing_keys:
                    raise Exception(
                        f"Prediction missing required keys: {missing_keys}")

                predicted_disease = prediction['predicted_disease']
                if predicted_disease is None or predicted_disease == '':
                    raise Exception("Predicted disease is null or empty")

                confidence_score = prediction['confidence_score']
                if confidence_score is None or np.isnan(confidence_score) or np.isinf(confidence_score):
                    raise Exception(
                        f"Invalid confidence score: {confidence_score}")

                all_predictions = prediction['all_predictions']
                if all_predictions is None:
                    raise Exception("All predictions is null")

                # Update prediction result with validated data
                prediction_result.predicted_disease = predicted_disease
                prediction_result.confidence_score = float(confidence_score)
                prediction_result.all_predictions = all_predictions
                prediction_result.save()

                # Generate Grad-CAM visualization for the predicted disease (primary)
                logger.info(
                    f"Generating Grad-CAM for primary prediction: {predicted_disease}")
                gradcam_available = False

                try:
                    gradcam_file = predictor.generate_gradcam_for_prediction(
                        prediction_result.xray_image.path,
                        predicted_disease
                    )

                    if gradcam_file:
                        prediction_result.gradcam_image.save(
                            f'gradcam_{prediction_result.id}_{predicted_disease}.png',
                            gradcam_file,
                            save=True
                        )
                        logger.info(
                            "Primary Grad-CAM image generated and saved successfully")
                        gradcam_available = True
                    else:
                        logger.warning("Primary Grad-CAM generation failed")

                except Exception as gradcam_error:
                    logger.error(
                        f"Primary Grad-CAM generation error: {str(gradcam_error)}")

                # OPTIONAL: Generate Grad-CAM for other diseases with high confidence
                # Uncomment this section if you want to pre-generate Grad-CAM for all diseases
                """
                CONFIDENCE_THRESHOLD = 0.3  # Adjust as needed
                for disease, confidence in all_predictions.items():
                    if disease != predicted_disease and confidence > CONFIDENCE_THRESHOLD:
                        try:
                            logger.info(f"Generating additional Grad-CAM for {disease} (confidence: {confidence:.3f})")
                            additional_gradcam = predictor.generate_gradcam_for_prediction(
                                prediction_result.xray_image.path,
                                disease
                            )
                            if additional_gradcam:
                                # You could save these to a separate field or file system
                                # For now, we'll just log success
                                logger.info(f"Additional Grad-CAM for {disease} generated successfully")
                        except Exception as e:
                            logger.warning(f"Failed to generate additional Grad-CAM for {disease}: {str(e)}")
                """

                # Serialize and return result
                result_serializer = PredictionResultSerializer(
                    prediction_result)

                return Response({
                    'success': True,
                    'message': 'Prediction completed successfully',
                    'data': result_serializer.data,
                    'gradcam_available': gradcam_available,
                    # Let frontend know which diseases are available
                    'available_diseases': list(all_predictions.keys())
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Prediction error: {str(e)}")
                if prediction_result and prediction_result.id:
                    try:
                        prediction_result.delete()
                    except Exception as delete_error:
                        logger.error(
                            f"Error deleting failed prediction: {delete_error}")

                return Response({
                    'success': False,
                    'message': f'Prediction failed: {str(e)}',
                    'debug_info': {
                        'models_loaded': len(predictor.models) if predictor.models else 0,
                        'available_models': list(predictor.models.keys()) if predictor.models else []
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if prediction_result and prediction_result.id:
            try:
                prediction_result.delete()
            except Exception as delete_error:
                logger.error(
                    f"Error deleting failed prediction: {delete_error}")

        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_gradcam_image(request, prediction_id):
    """
    Serve Grad-CAM visualization image
    """
    try:
        # Ensure user authentication
        if not request.user.is_authenticated:
            logger.error("Unauthenticated request for Grad-CAM image")
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)

        prediction = get_object_or_404(PredictionResult, id=prediction_id)

        # Get disease parameter if provided (for multiple disease support)
        disease = request.GET.get('disease')

        if disease and disease != prediction.predicted_disease:
            # Generate Grad-CAM for different disease if requested
            logger.info(
                f"Generating Grad-CAM for different disease: {disease}")
            try:
                gradcam_file = predictor.generate_gradcam_for_prediction(
                    prediction.xray_image.path,
                    disease
                )

                if gradcam_file:
                    # Read the content from ContentFile properly
                    gradcam_file.seek(0)  # Make sure we're at the beginning
                    image_data = gradcam_file.read()

                    response = HttpResponse(
                        image_data, content_type='image/png')
                    response['Content-Disposition'] = f'inline; filename="gradcam_{prediction_id}_{disease}.png"'
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    raise Http404(
                        f"Could not generate Grad-CAM for disease: {disease}")

            except Exception as e:
                logger.error(
                    f"Error generating Grad-CAM for {disease}: {str(e)}")
                raise Http404(f"Grad-CAM generation failed for {disease}")

        # Default behavior - serve the saved Grad-CAM image
        if not prediction.gradcam_image:
            # Try to generate it if it doesn't exist
            logger.info(
                f"Grad-CAM not found, attempting to generate for {prediction.predicted_disease}")
            try:
                gradcam_file = predictor.generate_gradcam_for_prediction(
                    prediction.xray_image.path,
                    prediction.predicted_disease
                )

                if gradcam_file:
                    prediction.gradcam_image.save(
                        f'gradcam_{prediction.id}_{prediction.predicted_disease}.png',
                        gradcam_file,
                        save=True
                    )
                else:
                    raise Http404("Grad-CAM image could not be generated")
            except Exception as e:
                logger.error(f"Error generating missing Grad-CAM: {str(e)}")
                raise Http404(
                    "Grad-CAM image not available and could not be generated")

        # Check if file exists
        if not os.path.exists(prediction.gradcam_image.path):
            logger.error(
                f"Grad-CAM file does not exist: {prediction.gradcam_image.path}")
            raise Http404("Grad-CAM file not found on disk")

        # Open and return the image file
        try:
            with open(prediction.gradcam_image.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/png')
                response['Content-Disposition'] = f'inline; filename="gradcam_{prediction_id}.png"'
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
        except IOError as e:
            logger.error(f"Error reading Grad-CAM file: {str(e)}")
            raise Http404("Could not read Grad-CAM image file")

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving Grad-CAM image: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_gradcam(request, prediction_id):
    """
    Regenerate Grad-CAM visualization for existing prediction
    """
    try:
        prediction = get_object_or_404(PredictionResult, id=prediction_id)

        if not prediction.predicted_disease:
            return Response({
                'success': False,
                'message': 'No predicted disease available for Grad-CAM generation'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get disease parameter if provided
        disease = request.data.get('disease', prediction.predicted_disease)

        logger.info(f"Regenerating Grad-CAM for disease: {disease}")

        # Generate new Grad-CAM
        gradcam_file = predictor.generate_gradcam_for_prediction(
            prediction.xray_image.path,
            disease
        )

        if gradcam_file:
            # Remove old Grad-CAM image if exists and we're updating the main one
            if disease == prediction.predicted_disease and prediction.gradcam_image:
                try:
                    prediction.gradcam_image.delete(save=False)
                except Exception as delete_error:
                    logger.warning(
                        f"Could not delete old Grad-CAM: {delete_error}")

            # Save new Grad-CAM image
            if disease == prediction.predicted_disease:
                prediction.gradcam_image.save(
                    f'gradcam_{prediction.id}_{disease}.png',
                    gradcam_file,
                    save=True
                )

            serializer = PredictionResultSerializer(prediction)
            return Response({
                'success': True,
                'message': f'Grad-CAM regenerated successfully for {disease}',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': f'Failed to generate Grad-CAM visualization for {disease}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error regenerating Grad-CAM: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_diseases(request):
    """
    Get list of diseases that can generate Grad-CAM
    """
    try:
        if predictor.models:
            diseases = list(predictor.models.keys())
            return Response({
                'success': True,
                'diseases': diseases,
                'count': len(diseases)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'No models loaded',
                'diseases': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}',
            'diseases': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Keep your existing functions...
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_predictions(request, patient_id):
    """
    Get all predictions for a specific patient
    """
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        predictions = PredictionResult.objects.filter(patient=patient)
        serializer = PredictionResultSerializer(predictions, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_predictions(request):
    """
    Get all predictions with optional filtering
    """
    try:
        predictions = PredictionResult.objects.all()

        # Optional filtering
        disease_filter = request.GET.get('disease')
        if disease_filter:
            predictions = predictions.filter(predicted_disease=disease_filter)

        confirmed_filter = request.GET.get('confirmed')
        if confirmed_filter is not None:
            predictions = predictions.filter(
                doctor_confirmed=confirmed_filter.lower() == 'true')

        serializer = PredictionResultSerializer(predictions, many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'count': predictions.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def confirm_prediction(request, prediction_id):
    """
    Allow doctor to confirm/reject a prediction
    """
    try:
        prediction = get_object_or_404(PredictionResult, id=prediction_id)

        # Assuming the user is a doctor (you might want to add proper doctor validation)
        doctor_confirmed = request.data.get('confirmed', False)
        prediction.doctor_confirmed = doctor_confirmed

        # You can also add the reviewing doctor if needed
        if hasattr(request.user, 'doctor_profile'):
            prediction.reviewed_by_doctor = request.user.doctor_profile

        prediction.save()

        serializer = PredictionResultSerializer(prediction)
        return Response({
            'success': True,
            'message': 'Prediction status updated',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
