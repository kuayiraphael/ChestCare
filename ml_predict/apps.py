#  ml_predict/apps.py
from django.apps import AppConfig


class MlModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_predict'

    def ready(self):
        # Pre-load models when Django starts
        from .utils import predictor
        print("ML models loaded successfully")
