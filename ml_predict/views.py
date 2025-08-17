# # from rest_framework import status
# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.response import Response
# # from django.shortcuts import get_object_or_404
# # from .models import PredictionResult
# # from .serializers import XrayPredictionSerializer, PredictionResultSerializer
# # from .utils import predictor
# # from dashboard.models import Patient
# # import logging

# # logger = logging.getLogger(__name__)


# # @api_view(['POST'])
# # @permission_classes([IsAuthenticated])
# # def predict_chest_disease(request):
# #     """
# #     Predict chest disease from X-ray image
# #     """
# #     try:
# #         serializer = XrayPredictionSerializer(data=request.data)
# #         if serializer.is_valid():
# #             patient_id = serializer.validated_data['patient_id']
# #             xray_image = serializer.validated_data['xray_image']

# #             # Get patient
# #             patient = get_object_or_404(Patient, id=patient_id)

# #             # Create prediction result instance
# #             prediction_result = PredictionResult(
# #                 patient=patient,
# #                 xray_image=xray_image
# #             )
# #             prediction_result.save()

# #             # Make prediction
# #             try:
# #                 prediction = predictor.predict(
# #                     prediction_result.xray_image.path)
                
# #                 # Validate prediction results
# #                 if not prediction or 'predicted_disease' not in prediction:
# #                     raise ValueError("Invalid prediction result")

# #                 # Update prediction result
# #                 prediction_result.predicted_disease = prediction['predicted_disease']
# #                 prediction_result.confidence_score = prediction['confidence_score']
# #                 prediction_result.all_predictions = prediction['all_predictions']
# #                 prediction_result.save()

# #                 # Serialize and return result
# #                 result_serializer = PredictionResultSerializer(
# #                     prediction_result)

# #                 return Response({
# #                     'success': True,
# #                     'message': 'Prediction completed successfully',
# #                     'data': result_serializer.data
# #                 }, status=status.HTTP_200_OK)

# #             except Exception as e:
# #                 logger.error(f"Prediction error: {str(e)}")
# #                 prediction_result.delete()  # Clean up failed prediction
# #                 return Response({
# #                     'success': False,
# #                     'message': f'Prediction failed: {str(e)}'
# #                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         else:
# #             return Response({
# #                 'success': False,
# #                 'message': 'Invalid data',
# #                 'errors': serializer.errors
# #             }, status=status.HTTP_400_BAD_REQUEST)

# #     except Exception as e:
# #         logger.error(f"Prediction error: {str(e)}")
# #         prediction_result.delete()
# #         return Response({
# #             'success': False,
# #             'message': f'Prediction failed: {str(e)}'
# #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
# # def get_patient_predictions(request, patient_id):
# #     """
# #     Get all predictions for a specific patient
# #     """
# #     try:
# #         patient = get_object_or_404(Patient, id=patient_id)
# #         predictions = PredictionResult.objects.filter(patient=patient)
# #         serializer = PredictionResultSerializer(predictions, many=True)

# #         return Response({
# #             'success': True,
# #             'data': serializer.data
# #         }, status=status.HTTP_200_OK)

# #     except Exception as e:
# #         return Response({
# #             'success': False,
# #             'message': str(e)
# #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
# # def get_all_predictions(request):
# #     """
# #     Get all predictions with optional filtering
# #     """
# #     try:
# #         predictions = PredictionResult.objects.all()

# #         # Optional filtering
# #         disease_filter = request.GET.get('disease')
# #         if disease_filter:
# #             predictions = predictions.filter(predicted_disease=disease_filter)

# #         confirmed_filter = request.GET.get('confirmed')
# #         if confirmed_filter is not None:
# #             predictions = predictions.filter(
# #                 doctor_confirmed=confirmed_filter.lower() == 'true')

# #         serializer = PredictionResultSerializer(predictions, many=True)

# #         return Response({
# #             'success': True,
# #             'data': serializer.data,
# #             'count': predictions.count()
# #         }, status=status.HTTP_200_OK)

# #     except Exception as e:
# #         return Response({
# #             'success': False,
# #             'message': str(e)
# #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # @api_view(['PATCH'])
# # @permission_classes([IsAuthenticated])
# # def confirm_prediction(request, prediction_id):
# #     """
# #     Allow doctor to confirm/reject a prediction
# #     """
# #     try:
# #         prediction = get_object_or_404(PredictionResult, id=prediction_id)

# #         # Assuming the user is a doctor (you might want to add proper doctor validation)
# #         doctor_confirmed = request.data.get('confirmed', False)
# #         prediction.doctor_confirmed = doctor_confirmed

# #         # You can also add the reviewing doctor if needed
# #         if hasattr(request.user, 'doctor_profile'):
# #             prediction.reviewed_by_doctor = request.user.doctor_profile

# #         prediction.save()

# #         serializer = PredictionResultSerializer(prediction)
# #         return Response({
# #             'success': True,
# #             'message': 'Prediction status updated',
# #             'data': serializer.data
# #         }, status=status.HTTP_200_OK)

# #     except Exception as e:
# #         return Response({
# #             'success': False,
# #             'message': str(e)
# #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from .models import PredictionResult
# from .serializers import XrayPredictionSerializer, PredictionResultSerializer
# from .utils import predictor
# from dashboard.models import Patient
# import logging

# logger = logging.getLogger(__name__)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def predict_chest_disease(request):
#     """
#     Predict chest disease from X-ray image
#     """
#     try:
#         serializer = XrayPredictionSerializer(data=request.data)
#         if serializer.is_valid():
#             patient_id = serializer.validated_data['patient_id']
#             xray_image = serializer.validated_data['xray_image']

#             # Get patient
#             patient = get_object_or_404(Patient, id=patient_id)

#             # Create prediction result instance but don't save yet
#             prediction_result = PredictionResult(
#                 patient=patient,
#                 xray_image=xray_image
#             )

#             # Save to get the file path (needed for prediction)
#             prediction_result.save()

#             # Make prediction
#             try:
#                 logger.info(
#                     f"Starting prediction for image: {prediction_result.xray_image.path}")

#                 # Check if predictor has loaded models
#                 if not predictor.models:
#                     raise Exception(
#                         "No ML models loaded. Please check model files and logs.")

#                 prediction = predictor.predict(
#                     prediction_result.xray_image.path)

#                 # Validate prediction results
#                 if not prediction:
#                     raise Exception("Prediction returned None")

#                 if 'predicted_disease' not in prediction:
#                     raise Exception(
#                         "Prediction missing 'predicted_disease' key")

#                 if 'confidence_score' not in prediction:
#                     raise Exception(
#                         "Prediction missing 'confidence_score' key")

#                 if prediction['confidence_score'] is None:
#                     raise Exception(
#                         "Prediction returned null confidence_score")

#                 # Update prediction result
#                 prediction_result.predicted_disease = prediction['predicted_disease']
#                 prediction_result.confidence_score = prediction['confidence_score']
#                 prediction_result.all_predictions = prediction['all_predictions']
#                 prediction_result.save()

#                 # Serialize and return result
#                 result_serializer = PredictionResultSerializer(
#                     prediction_result)

#                 return Response({
#                     'success': True,
#                     'message': 'Prediction completed successfully',
#                     'data': result_serializer.data
#                 }, status=status.HTTP_200_OK)

#             except Exception as e:
#                 logger.error(f"Prediction error: {str(e)}")
#                 # Clean up - only delete if the record was saved (has an id)
#                 if prediction_result.id:
#                     prediction_result.delete()

#                 return Response({
#                     'success': False,
#                     'message': f'Prediction failed: {str(e)}',
#                     'debug_info': {
#                         'models_loaded': len(predictor.models),
#                         'available_models': list(predictor.models.keys()) if predictor.models else []
#                     }
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         else:
#             return Response({
#                 'success': False,
#                 'message': 'Invalid data',
#                 'errors': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

#     except Exception as e:
#         logger.error(f"Unexpected error: {str(e)}")
#         return Response({
#             'success': False,
#             'message': f'Server error: {str(e)}'
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # Add this debug endpoint to check ML model status
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def check_ml_models(request):
#     """
#     Check ML model loading status
#     """
#     try:
#         model_status = {}
#         for disease in predictor.model_paths.keys():
#             model_status[disease] = {
#                 'loaded': disease in predictor.models,
#                 'path_exists': predictor.model_paths.get(disease, '') != ''
#             }

#         return Response({
#             'success': True,
#             'models_loaded': len(predictor.models),
#             'total_models': len(predictor.model_paths),
#             'model_status': model_status,
#             'predictor_available': predictor is not None
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({
#             'success': False,
#             'message': f'Error checking models: {str(e)}'
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_patient_predictions(request, patient_id):
#     """
#     Get all predictions for a specific patient
#     """
#     try:
#         patient = get_object_or_404(Patient, id=patient_id)
#         predictions = PredictionResult.objects.filter(patient=patient)
#         serializer = PredictionResultSerializer(predictions, many=True)

#         return Response({
#             'success': True,
#             'data': serializer.data
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({
#             'success': False,
#             'message': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_all_predictions(request):
#     """
#     Get all predictions with optional filtering
#     """
#     try:
#         predictions = PredictionResult.objects.all()

#         # Optional filtering
#         disease_filter = request.GET.get('disease')
#         if disease_filter:
#             predictions = predictions.filter(predicted_disease=disease_filter)

#         confirmed_filter = request.GET.get('confirmed')
#         if confirmed_filter is not None:
#             predictions = predictions.filter(
#                 doctor_confirmed=confirmed_filter.lower() == 'true')

#         serializer = PredictionResultSerializer(predictions, many=True)

#         return Response({
#             'success': True,
#             'data': serializer.data,
#             'count': predictions.count()
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({
#             'success': False,
#             'message': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def confirm_prediction(request, prediction_id):
#     """
#     Allow doctor to confirm/reject a prediction
#     """
#     try:
#         prediction = get_object_or_404(PredictionResult, id=prediction_id)

#         # Assuming the user is a doctor (you might want to add proper doctor validation)
#         doctor_confirmed = request.data.get('confirmed', False)
#         prediction.doctor_confirmed = doctor_confirmed

#         # You can also add the reviewing doctor if needed
#         if hasattr(request.user, 'doctor_profile'):
#             prediction.reviewed_by_doctor = request.user.doctor_profile

#         prediction.save()

#         serializer = PredictionResultSerializer(prediction)
#         return Response({
#             'success': True,
#             'message': 'Prediction status updated',
#             'data': serializer.data
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({
#             'success': False,
#             'message': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
import numpy as np

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_chest_disease(request):
    """
    Predict chest disease from X-ray image
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

                # Comprehensive validation of prediction results
                if not prediction:
                    raise Exception("Prediction returned None or empty result")

                # Validate required keys
                required_keys = ['predicted_disease',
                                 'confidence_score', 'all_predictions']
                missing_keys = [
                    key for key in required_keys if key not in prediction]
                if missing_keys:
                    raise Exception(
                        f"Prediction missing required keys: {missing_keys}")

                # Validate predicted_disease
                predicted_disease = prediction['predicted_disease']
                if predicted_disease is None or predicted_disease == '':
                    raise Exception("Predicted disease is null or empty")

                # Validate confidence_score
                confidence_score = prediction['confidence_score']
                if confidence_score is None:
                    raise Exception("Confidence score is null")

                if np.isnan(confidence_score) or np.isinf(confidence_score):
                    raise Exception(
                        f"Confidence score is invalid: {confidence_score}")

                if not isinstance(confidence_score, (int, float)):
                    raise Exception(
                        f"Confidence score is not a number: {type(confidence_score)}")

                # Validate all_predictions
                all_predictions = prediction['all_predictions']
                if all_predictions is None:
                    raise Exception("All predictions is null")

                # Update prediction result with validated data
                prediction_result.predicted_disease = predicted_disease
                prediction_result.confidence_score = float(confidence_score)
                prediction_result.all_predictions = all_predictions
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

                # Clean up - only delete if the record was saved (has an id)
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
                        'models_loaded': len(predictor.models),
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

        # Clean up prediction result if it exists
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
def check_ml_models(request):
    """
    Check ML model loading status
    """
    try:
        model_status = {}
        for disease in predictor.model_paths.keys():
            model_path = os.path.join(
                settings.ML_PREDICT_PATH, predictor.model_paths[disease])
            model_status[disease] = {
                'loaded': disease in predictor.models,
                'path_exists': os.path.exists(model_path),
                'model_path': model_path
            }

        return Response({
            'success': True,
            'models_loaded': len(predictor.models),
            'total_models': len(predictor.model_paths),
            'model_status': model_status,
            'predictor_available': predictor is not None,
            'ml_predict_path': getattr(settings, 'ML_PREDICT_PATH', 'NOT SET')
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error checking models: {str(e)}'
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
