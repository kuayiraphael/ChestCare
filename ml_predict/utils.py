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

    def preprocess_image(self, image_path, target_size=(224, 224)):
        """Preprocess X-ray image for prediction"""
        try:
            # Load and preprocess image
            image = Image.open(image_path)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize image
            image = image.resize(target_size)

            # Convert to numpy array and normalize
            image_array = np.array(image) / 255.0

            # Add batch dimension
            image_array = np.expand_dims(image_array, axis=0)

            return image_array

        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise

    def predict(self, image_path):
        """Make predictions using all loaded models"""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)

            predictions = {}

            # Make predictions with each model
            for disease, model in self.models.items():
                try:
                    prediction = model.predict(processed_image, verbose=0)
                    confidence = float(prediction[0][0] if prediction[0].shape[0] == 1
                                       else np.max(prediction[0]))
                    predictions[disease] = confidence
                except Exception as e:
                    logger.error(f"Error predicting {disease}: {str(e)}")
                    predictions[disease] = 0.0

            # Find the disease with highest confidence
            if predictions:
                best_prediction = max(predictions.items(), key=lambda x: x[1])
                return {
                    'predicted_disease': best_prediction[0],
                    'confidence_score': best_prediction[1],
                    'all_predictions': predictions
                }
            else:
                raise Exception("No valid predictions made")

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise


# Global predictor instance
predictor = ChestXrayPredictor()
