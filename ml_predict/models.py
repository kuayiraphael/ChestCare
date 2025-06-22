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
    predicted_disease = models.CharField(max_length=50, choices=DISEASE_TYPES)
    confidence_score = models.FloatField()
    all_predictions = models.JSONField()  # Stores all model predictions
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
        return f"{self.patient} - {self.predicted_disease} ({self.confidence_score:.2f})"
