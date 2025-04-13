# dashboard/api_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import (
    Disease,
    Patient,
    Doctor,
    DiseaseCase,
    Appointment,
    Symptom,
    PatientSymptomRecord
)
from .serializers import (
    DiseaseSerializer,
    PatientSerializer,
    DoctorSerializer,
    DiseaseCaseSerializer,
    AppointmentSerializer,
    SymptomSerializer,
    PatientSymptomRecordSerializer
)


class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [IsAuthenticated]


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]


class DiseaseCaseViewSet(viewsets.ModelViewSet):
    queryset = DiseaseCase.objects.all()
    serializer_class = DiseaseCaseSerializer
    permission_classes = [IsAuthenticated]


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]


class SymptomViewSet(viewsets.ModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [IsAuthenticated]


class PatientSymptomRecordViewSet(viewsets.ModelViewSet):
    queryset = PatientSymptomRecord.objects.all()
    serializer_class = PatientSymptomRecordSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_summary(request):
    """API endpoint for dashboard summary"""
    disease_count = Disease.objects.count()
    patient_count = Patient.objects.count()
    appointment_count = Appointment.objects.count()
    doctor_count = Doctor.objects.count()

    return Response({
        'disease_count': disease_count,
        'patient_count': patient_count,
        'appointment_count': appointment_count,
        'doctor_count': doctor_count
    })
