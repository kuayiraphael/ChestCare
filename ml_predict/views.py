from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import PredictionResult
from .serializers import XrayPredictionSerializer, PredictionResultSerializer
from .utils import predictor
from dashboard.models import Patient
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_chest_disease(request):
    """
    Predict chest disease from X-ray image
    """
    try:
        serializer = XrayPredictionSerializer(data=request.data)
        if serializer.is_valid():
            patient_id = serializer.validated_data['patient_id']
            xray_image = serializer.validated_data['xray_image']

            # Get patient
            patient = get_object_or_404(Patient, id=patient_id)

            # Create prediction result instance
            prediction_result = PredictionResult(
                patient=patient,
                xray_image=xray_image
            )
            prediction_result.save()

            # Make prediction
            try:
                prediction = predictor.predict(
                    prediction_result.xray_image.path)

                # Update prediction result
                prediction_result.predicted_disease = prediction['predicted_disease']
                prediction_result.confidence_score = prediction['confidence_score']
                prediction_result.all_predictions = prediction['all_predictions']
                prediction_result.save()

                # Serialize and return result
                result_serializer = PredictionResultSerializer(
                    prediction_result)

                return Response({
                    'success': True,
                    'message': 'Prediction completed successfully',
                    'data': result_serializer.data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Prediction error: {str(e)}")
                prediction_result.delete()  # Clean up failed prediction
                return Response({
                    'success': False,
                    'message': f'Prediction failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
