import os
import numpy as np
import tensorflow as tf
from PIL import Image
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


class ChestXrayPredictor:
    def __init__(self):
        self.models = {}
        self.model_paths = {
            'cardiomegaly': 'cardiomegaly_model.keras',
            'pneumonia': 'pneumonia_model.keras',
            'tuberculosis': 'tuberculosis_model.keras',
            'pulmonary_hypertension': 'pulmonary_hypertension_model.keras'
        }
        self.load_models()

    def load_models(self):
        """Load all ML models on initialization"""
        failed_models = []
        error_models = []
        for disease, model_file in self.model_paths.items():
            model_path = os.path.join(
                str(settings.ML_PREDICT_PATH), model_file)
            if os.path.exists(model_path):
                try:
                    self.models[disease] = tf.keras.models.load_model(
                        model_path)
                    logger.info(f"Loaded {disease} model successfully")
                except Exception as e:
                    logger.error(f"Error loading {disease} model: {str(e)}")
                    error_models.append(disease)
            else:
                logger.warning(f"Model file not found: {model_path}")
                failed_models.append(disease)

        if not failed_models and not error_models:
            logger.info("ML models loaded successfully")
        else:
            if failed_models:
                logger.error(
                    f"The following models were not found: {', '.join(failed_models)}")
            if error_models:
                logger.error(
                    f"The following models failed to load: {', '.join(error_models)}")

    # def preprocess_image(self, image_path, target_size=(28, 28)):
    #     """Preprocess X-ray image for prediction"""
    #     try:
    #         # Load and preprocess image
    #         image = Image.open(image_path)

    #         # Convert to RGB if necessary
    #         if image.mode != 'RGB':
    #             image = image.convert('RGB')

    #         # Resize image
    #         image = image.resize(target_size)

    #         # Convert to numpy array and normalize
    #         image_array = np.array(image) / 255.0

    #         # Add batch dimension
    #         image_array = np.expand_dims(image_array, axis=0)

    #         return image_array

    #     except Exception as e:
    #         logger.error(f"Error preprocessing image: {str(e)}")
    #         raise
    def preprocess_image(self, image_path, model):
        """Preprocess image to match specific model's requirements"""
        # Get the size the model actually expects
        target_size = (model.input_shape[1], model.input_shape[2])

        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        image = image.resize(target_size)
        image_array = np.array(image) / 255.0
        return np.expand_dims(image_array, axis=0)

    def predict(self, image_path):
        """Make predictions using all loaded models"""
        try:
            # Check if any models are loaded
            if not self.models:
                raise Exception("No ML models are loaded")

            # Preprocess image

            predictions = {}

            # Make predictions with each model
            for disease, model in self.models.items():
                try:
                    processed_image = self.preprocess_image(image_path, model)
                    prediction = model.predict(processed_image, verbose=0)

                    # Better prediction handling
                    if prediction is None or len(prediction) == 0:
                        logger.warning(
                            f"Model {disease} returned empty prediction")
                        confidence = 0.0
                    else:
                        # Handle different prediction output formats
                        pred_array = prediction[0]
                        if pred_array.shape[0] == 1:
                            confidence = float(pred_array[0])
                        else:
                            confidence = float(np.max(pred_array))

                        # Ensure confidence is a valid number
                        if np.isnan(confidence) or np.isinf(confidence):
                            logger.warning(
                                f"Invalid confidence score for {disease}: {confidence}")
                            confidence = 0.0

                        # Clamp confidence between 0 and 1
                        confidence = max(0.0, min(1.0, confidence))

                    predictions[disease] = confidence
                    logger.info(f"Prediction for {disease}: {confidence:.4f}")

                except Exception as e:
                    logger.error(f"Error predicting {disease}: {str(e)}")
                    predictions[disease] = 0.0

            # Validate predictions
            if not predictions:
                raise Exception("No predictions were generated")

            # Find the disease with highest confidence
            valid_predictions = {
                k: v for k, v in predictions.items() if v is not None and not np.isnan(v)}

            if not valid_predictions:
                raise Exception("All predictions returned invalid values")

            best_prediction = max(
                valid_predictions.items(), key=lambda x: x[1])

            # Ensure we have valid results
            predicted_disease = best_prediction[0]
            confidence_score = best_prediction[1]

            # Final validation
            if predicted_disease is None or confidence_score is None:
                raise Exception("Best prediction contains null values")

            if np.isnan(confidence_score) or np.isinf(confidence_score):
                raise Exception(
                    f"Best prediction confidence is invalid: {confidence_score}")

            result = {
                'predicted_disease': predicted_disease,
                'confidence_score': confidence_score,
                'all_predictions': valid_predictions
            }

            logger.info(f"Final prediction result: {result}")
            return result

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise


# Global predictor instance
predictor = ChestXrayPredictor()
