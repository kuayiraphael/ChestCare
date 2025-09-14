import os
import numpy as np
import tensorflow as tf
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
import json
import logging
import cv2
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from io import BytesIO

logger = logging.getLogger(__name__)


class GradCAMGenerator:
    """Class to generate Grad-CAM visualizations"""

    def __init__(self, model, layer_name=None):
        self.model = model
        self.layer_name = layer_name or self._find_last_conv_layer()
        # Initialize the model by running a dummy prediction
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the model with a dummy input to ensure all layers are built"""
        try:
            # Get input shape and create dummy input
            input_shape = self.model.input_shape
            if input_shape[0] is None:
                # Batch dimension is None, create with batch size 1
                dummy_shape = (1,) + input_shape[1:]
            else:
                dummy_shape = input_shape

            dummy_input = tf.zeros(dummy_shape, dtype=tf.float32)

            # Run a dummy prediction to build all layers
            _ = self.model(dummy_input, training=False)
            logger.info(f"Model initialized successfully for Grad-CAM")

        except Exception as e:
            logger.warning(
                f"Could not initialize model for Grad-CAM: {str(e)}")

    def _find_last_conv_layer(self):
        """Find the last convolutional layer in the model"""
        conv_layers = []

        def find_conv_recursive(layer):
            if hasattr(layer, 'layers'):  # Composite layer (like Sequential, Model)
                for sublayer in layer.layers:
                    find_conv_recursive(sublayer)
            elif 'conv' in layer.__class__.__name__.lower():
                conv_layers.append(layer.name)

        # Search through the model
        if hasattr(self.model, 'layers'):
            for layer in self.model.layers:
                find_conv_recursive(layer)

        if conv_layers:
            logger.info(f"Found conv layers: {conv_layers}")
            return conv_layers[-1]  # Return last conv layer

        logger.warning("No convolutional layers found for Grad-CAM")
        return None

    def generate_gradcam(self, img_array, class_index=0):
        """Generate Grad-CAM heatmap for given image and class"""
        try:
            if self.layer_name is None:
                logger.warning("No convolutional layer found for Grad-CAM")
                return None

            # Ensure input array has the correct shape
            if len(img_array.shape) == 3:
                img_array = np.expand_dims(img_array, axis=0)

            # Verify the target layer exists and is accessible
            try:
                target_layer = self.model.get_layer(self.layer_name)
            except ValueError as e:
                logger.error(
                    f"Could not find layer {self.layer_name}: {str(e)}")
                return None

            # Create a model that maps the input image to the activations of the target conv layer
            # as well as the output predictions
            try:
                grad_model = tf.keras.models.Model(
                    self.model.input,
                    [target_layer.output, self.model.output]
                )
            except Exception as e:
                logger.error(f"Could not create gradient model: {str(e)}")
                return None

            # Convert to tensor with correct dtype
            img_tensor = tf.convert_to_tensor(img_array, dtype=tf.float32)

            # Compute the gradient of the top predicted class for our input image
            # with respect to the activations of the target conv layer
            with tf.GradientTape() as tape:
                try:
                    conv_outputs, predictions = grad_model(
                        img_tensor, training=False)

                    if len(predictions.shape) > 1 and predictions.shape[1] > 1:
                        # Multi-class output
                        class_output = predictions[:, class_index]
                    else:
                        # Binary classification
                        class_output = predictions

                except Exception as e:
                    logger.error(f"Error in forward pass: {str(e)}")
                    return None

            # Extract the gradients of the top predicted class
            try:
                grads = tape.gradient(class_output, conv_outputs)

                if grads is None:
                    logger.error(
                        "Gradients are None - this might indicate a disconnected graph")
                    return None

            except Exception as e:
                logger.error(f"Error computing gradients: {str(e)}")
                return None

            # Pool the gradients over all the axes leaving out the channel dimension
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

            # Weight the channels by corresponding gradients
            conv_outputs = conv_outputs[0]
            heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)

            # Normalize the heatmap between 0 & 1 for visualization
            heatmap_max = tf.math.reduce_max(heatmap)
            if heatmap_max > 0:
                heatmap = tf.maximum(heatmap, 0) / heatmap_max
            else:
                heatmap = tf.zeros_like(heatmap)

            return heatmap.numpy()

        except Exception as e:
            logger.error(f"Error generating Grad-CAM: {str(e)}")
            return None

    def create_overlay_image(self, original_image_path, heatmap):
        """Create overlay of original image and heatmap"""
        try:
            # Load original image
            original_img = cv2.imread(original_image_path)
            if original_img is None:
                logger.error(f"Could not load image: {original_image_path}")
                return None

            original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

            # Resize heatmap to match original image size
            img_height, img_width = original_img.shape[:2]
            heatmap_resized = cv2.resize(heatmap, (img_width, img_height))

            # Apply colormap to heatmap
            heatmap_colored = cm.jet(heatmap_resized)[
                :, :, :3]  # Remove alpha channel
            heatmap_colored = (heatmap_colored * 255).astype(np.uint8)

            # Create overlay
            overlay = cv2.addWeighted(
                original_img, 0.6, heatmap_colored, 0.4, 0)

            return overlay

        except Exception as e:
            logger.error(f"Error creating overlay image: {str(e)}")
            return None

class ChestXrayPredictor:
    def __init__(self):
        self.models = {}
        self.gradcam_generators = {}  # New: Store Grad-CAM generators
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
                    model = tf.keras.models.load_model(model_path)
                    self.models[disease] = model
                    # Initialize Grad-CAM generator for each model
                    self.gradcam_generators[disease] = GradCAMGenerator(model)
                    logger.info(
                        f"Loaded {disease} model successfully with Grad-CAM")
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

    def generate_gradcam_for_prediction(self, image_path, disease, confidence_threshold=0.1):
        """Generate Grad-CAM visualization for the predicted disease"""
        try:
            if disease not in self.models or disease not in self.gradcam_generators:
                logger.warning(
                    f"Model or Grad-CAM generator not available for {disease}")
                return None

            model = self.models[disease]
            gradcam_gen = self.gradcam_generators[disease]

            # Preprocess image
            processed_image = self.preprocess_image(image_path, model)

            # Generate Grad-CAM heatmap
            heatmap = gradcam_gen.generate_gradcam(processed_image)

            if heatmap is None:
                logger.warning(f"Failed to generate Grad-CAM for {disease}")
                return None

            # Create overlay image
            overlay_image = gradcam_gen.create_overlay_image(
                image_path, heatmap)

            if overlay_image is None:
                logger.warning(f"Failed to create overlay image for {disease}")
                return None

            # Convert to PIL Image and save to BytesIO
            overlay_pil = Image.fromarray(overlay_image)
            buffer = BytesIO()
            overlay_pil.save(buffer, format='PNG')
            buffer.seek(0)

            return ContentFile(buffer.getvalue(), name=f'gradcam_{disease}.png')

        except Exception as e:
            logger.error(f"Error generating Grad-CAM for {disease}: {str(e)}")
            return None

    def predict(self, image_path):
        """Make predictions using all loaded models"""
        try:
            # Check if any models are loaded
            if not self.models:
                raise Exception("No ML models are loaded")

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
