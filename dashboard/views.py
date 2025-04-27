# dashboard/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Disease,
    Patient,
    Doctor,
    DiseaseCase,
    Appointment,
    Symptom,
    PatientSymptomRecord,
    DiseaseStatistic
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

import json
from datetime import datetime, timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_home(request):
    """API endpoint for dashboard homepage data"""
    # Get the doctor instance for the logged-in user if applicable
    try:
        doctor = request.user.doctor_profile
        is_doctor = True
    except:
        doctor = None
        is_doctor = False

    # Get counts for summary cards
    patient_count = Patient.objects.count()
    active_case_count = DiseaseCase.objects.filter(status='active').count()
    appointment_count = Appointment.objects.filter(status='scheduled').count()

    # For the doctor's specific counts if they are a doctor
    if doctor:
        doctor_patient_count = DiseaseCase.objects.filter(
            doctor=doctor).values('patient').distinct().count()
        doctor_active_case_count = DiseaseCase.objects.filter(
            doctor=doctor, status='active').count()
        doctor_appointment_count = Appointment.objects.filter(
            doctor=doctor, status='scheduled').count()
    else:
        doctor_patient_count = 0
        doctor_active_case_count = 0
        doctor_appointment_count = 0

    # Get disease distribution data
    diseases = Disease.objects.all()
    disease_distribution = []
    for disease in diseases:
        case_count = DiseaseCase.objects.filter(disease=disease).count()
        disease_distribution.append({
            'name': disease.name,
            'count': case_count
        })

    # Get upcoming appointments for the doctor
    if doctor:
        today = timezone.now().date()
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            date__gte=today,
            status='scheduled'
        ).order_by('date', 'time')[:5]

        serialized_appointments = AppointmentSerializer(
            upcoming_appointments, many=True).data
    else:
        serialized_appointments = []

    # Get recent patients
    recent_patients = Patient.objects.all().order_by('-created_at')[:5]
    serialized_patients = PatientSerializer(recent_patients, many=True).data

    response_data = {
        'summary': {
            'patient_count': patient_count,
            'active_case_count': active_case_count,
            'appointment_count': appointment_count,
        },
        'doctor_summary': {
            'is_doctor': is_doctor,
            'patient_count': doctor_patient_count,
            'active_case_count': doctor_active_case_count,
            'appointment_count': doctor_appointment_count,
        },
        'disease_distribution': disease_distribution,
        'upcoming_appointments': serialized_appointments,
        'recent_patients': serialized_patients
    }

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def disease_trends(request):
    """API endpoint for disease trends data"""
    diseases = Disease.objects.all()
    serialized_diseases = DiseaseSerializer(diseases, many=True).data

    # Default to showing last 12 months of data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)

    response_data = {
        'diseases': serialized_diseases,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }

    return Response(response_data)

# Update the get_disease_data function in dashboard/views.py


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_disease_data(request, disease_type):
    """API endpoint to get disease data for charts"""
    try:
        # Get the disease by type
        disease = Disease.objects.get(type=disease_type)

        # Get time range from query parameters or use defaults
        months = int(request.query_params.get('months', 12))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30*months)

        # Get statistics for this disease
        stats = DiseaseStatistic.objects.filter(
            disease=disease,
            year__gte=start_date.year,
            year__lte=end_date.year
        ).order_by('year', 'month')

        # Filter for the correct months if spanning multiple years
        if start_date.year == end_date.year:
            stats = stats.filter(month__gte=start_date.month,
                                 month__lte=end_date.month)

        # Format the data for charts
        data = []
        for stat in stats:
            # Format month/year for display
            month_name = datetime(2000, stat.month, 1).strftime('%B')
            period = f"{month_name} {stat.year}"

            data.append({
                'period': period,
                'count': stat.case_count,
                'percent_change': stat.percent_change
            })

        response_data = {
            'disease_name': disease.name,
            'disease_type': disease.type,
            'disease_description': disease.description,
            'data': data
        }

        return Response(response_data)

    except Disease.DoesNotExist:
        return Response({'error': 'Disease not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_appointments(request):
    """API endpoint to get appointments for the calendar"""
    try:
        doctor = request.user.doctor_profile
        appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=['scheduled', 'rescheduled']
        )

        events = []
        for appointment in appointments:
            events.append({
                'id': appointment.id,
                'title': f"{appointment.patient.first_name} {appointment.patient.last_name}",
                'start': f"{appointment.date.isoformat()}T{appointment.time.isoformat()}",
                'type': appointment.appointment_type,
                'status': appointment.status,
                'patient_id': appointment.patient.id
            })

        return Response(events)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patients_by_status(request):
    """API endpoint to get patients grouped by status"""
    statuses = Patient.STATUS_CHOICES
    result = {}

    for status_code, status_name in statuses:
        patients = Patient.objects.filter(status=status_code)
        serialized_patients = PatientSerializer(patients, many=True).data
        result[status_code] = {
            'name': status_name,
            'count': patients.count(),
            'patients': serialized_patients
        }

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_details(request, patient_id):
    """API endpoint to get detailed patient information with related data"""
    try:
        patient = Patient.objects.get(pk=patient_id)

        # Serialize patient data
        patient_data = PatientSerializer(patient).data

        # Get disease cases for this patient
        disease_cases = DiseaseCase.objects.filter(patient=patient)
        cases_data = DiseaseCaseSerializer(disease_cases, many=True).data

        # Get appointments for this patient
        appointments = Appointment.objects.filter(
            patient=patient).order_by('-date', '-time')
        appointments_data = AppointmentSerializer(appointments, many=True).data

        # Get symptom records for this patient
        symptom_records = PatientSymptomRecord.objects.filter(
            patient=patient).order_by('-recorded_date')
        symptom_data = PatientSymptomRecordSerializer(
            symptom_records, many=True).data

        response_data = {
            'patient': patient_data,
            'disease_cases': cases_data,
            'appointments': appointments_data,
            'symptom_records': symptom_data
        }

        return Response(response_data)

    except Patient.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_disease_case(request):
    """API endpoint to create a new disease case"""
    try:
        # Get the doctor from the request user
        doctor = request.user.doctor_profile

        # Add doctor to the data
        data = request.data.copy()
        data['doctor'] = doctor.id

        serializer = DiseaseCaseSerializer(data=data)
        if serializer.is_valid():
            disease_case = serializer.save()

            # Update patient status to diagnosed
            patient = disease_case.patient
            patient.status = 'diagnosed'
            patient.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_appointment(request):
    """API endpoint to create a new appointment"""
    try:
        # Get the doctor from the request user
        doctor = request.user.doctor_profile

        # Add doctor to the data
        data = request.data.copy()
        data['doctor'] = doctor.id

        serializer = AppointmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_patient_symptom(request, patient_id):
    """API endpoint to add a symptom record for a patient"""
    try:
        patient = get_object_or_404(Patient, id=patient_id)

        # Add patient to the data
        data = request.data.copy()
        data['patient'] = patient_id

        serializer = PatientSymptomRecordSerializer(data=data)
        if serializer.is_valid():
            symptom_record = serializer.save()

            # Add to patient's symptoms as well
            patient.symptoms.add(symptom_record.symptom)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_patients(request):
    """API endpoint to get patients for the logged-in doctor"""
    try:
        doctor = request.user.doctor_profile

        # Get distinct patients from disease cases
        patient_ids = DiseaseCase.objects.filter(
            doctor=doctor).values_list('patient', flat=True).distinct()
        patients = Patient.objects.filter(id__in=patient_ids)

        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_appointments(request):
    """API endpoint to get appointments for the logged-in doctor"""
    try:
        doctor = request.user.doctor_profile

        # Get filter parameters
        status_filter = request.query_params.get('status', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)

        # Base query
        appointments = Appointment.objects.filter(doctor=doctor)

        # Apply filters
        if status_filter:
            appointments = appointments.filter(status=status_filter)

        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                appointments = appointments.filter(date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                appointments = appointments.filter(date__lte=date_to)
            except ValueError:
                pass

        # Order by date and time
        appointments = appointments.order_by('date', 'time')

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
