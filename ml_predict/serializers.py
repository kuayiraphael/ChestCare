from rest_framework import serializers
from .models import PredictionResult
from dashboard.models import Patient


class XrayPredictionSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    xray_image = serializers.ImageField()

    def validate_patient_id(self, value):
        try:
            Patient.objects.get(id=value)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found")
        return value


class PredictionResultSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = PredictionResult
        fields = [
            'id', 'patient', 'patient_name', 'xray_image',
            'predicted_disease', 'confidence_score', 'all_predictions',
            'created_at', 'reviewed_by_doctor', 'doctor_confirmed'
        ]
        read_only_fields = ['id', 'created_at']

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
