# from django.db import models
# from django.contrib.auth import get_user_model
# from dashboard.models import Patient, Disease

# User = get_user_model()


# class PredictionResult(models.Model):
#     DISEASE_TYPES = [
#         ('cardiomegaly', 'Cardiomegaly'),
#         ('pneumonia', 'Pneumonia'),
#         ('tuberculosis', 'Tuberculosis'),
#         ('pulmonary_hypertension', 'Pulmonary Hypertension'),
#     ]

#     patient = models.ForeignKey(
#         Patient, on_delete=models.CASCADE, related_name='predictions')
#     xray_image = models.ImageField(upload_to='xray_uploads/')
#     predicted_disease = models.CharField(
#         max_length=50, choices=DISEASE_TYPES, null=True, blank=True)
#     confidence_score = models.FloatField(
#         null=True, blank=True)  # Allow null values
#     all_predictions = models.JSONField(
#         null=True, blank=True)  # Allow null values
#     created_at = models.DateTimeField(auto_now_add=True)
#     reviewed_by_doctor = models.ForeignKey(
#         'dashboard.Doctor',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     doctor_confirmed = models.BooleanField(default=False)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         if self.predicted_disease and self.confidence_score:
#             return f"{self.patient} - {self.predicted_disease} ({self.confidence_score:.2f})"
#         return f"{self.patient} - Prediction Failed"

from django.db import models
from django.contrib.auth import get_user_model
from dashboard.models import Patient, Disease

User = get_user_model()


class PredictionResult(models.Model):
    DISEASE_TYPES = [
        ('cardiomegaly', 'Cardiomegaly'),
        ('pneumonia', 'Pneumonia'),
        ('tuberculosis', 'Tuberculosis'),
        ('pulmonary_hypertension', 'Pulmonary Hypertension'),
    ]

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='predictions')
    xray_image = models.ImageField(upload_to='xray_uploads/')
    gradcam_image = models.ImageField(
        upload_to='gradcam_uploads/', null=True, blank=True)  # New field
    predicted_disease = models.CharField(
        max_length=50, choices=DISEASE_TYPES, null=True, blank=True)
    confidence_score = models.FloatField(
        null=True, blank=True)  # Allow null values
    all_predictions = models.JSONField(
        null=True, blank=True)  # Allow null values
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by_doctor = models.ForeignKey(
        'dashboard.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    doctor_confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.predicted_disease and self.confidence_score:
            return f"{self.patient} - {self.predicted_disease} ({self.confidence_score:.2f})"
        return f"{self.patient} - Prediction Failed"
