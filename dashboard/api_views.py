# dashboard/api_views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone

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


class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='statistics')
    def get_disease_statistics(self, request, pk=None):
        """Get statistics for a specific disease"""
        disease = self.get_object()
        stats = DiseaseStatistic.objects.filter(
            disease=disease
        ).order_by('year', 'month')

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

    @action(detail=False, methods=['get'], url_path='by-type/(?P<disease_type>[^/.]+)')
    def get_by_type(self, request, disease_type=None):
        """Get disease by type"""
        try:
            disease = Disease.objects.get(type=disease_type)
            serializer = self.get_serializer(disease)
            return Response(serializer.data)
        except Disease.DoesNotExist:
            return Response({'error': 'Disease not found'}, status=status.HTTP_404_NOT_FOUND)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='details')
    def get_patient_details(self, request, pk=None):
        """Get detailed patient information with related data"""
        patient = self.get_object()

        # Serialize patient data
        patient_data = self.get_serializer(patient).data

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

    @action(detail=False, methods=['get'], url_path='by-status')
    def patients_by_status(self, request):
        """Get patients grouped by status"""
        statuses = Patient.STATUS_CHOICES
        result = {}

        for status_code, status_name in statuses:
            patients = Patient.objects.filter(status=status_code)
            serialized_patients = self.get_serializer(patients, many=True).data
            result[status_code] = {
                'name': status_name,
                'count': patients.count(),
                'patients': serialized_patients
            }

        return Response(result)

    @action(detail=True, methods=['post'], url_path='add-symptom')
    def add_symptom(self, request, pk=None):
        """Add a symptom record for a patient"""
        patient = self.get_object()

        # Add patient to the data
        data = request.data.copy()
        data['patient'] = patient.id

        serializer = PatientSymptomRecordSerializer(data=data)
        if serializer.is_valid():
            symptom_record = serializer.save()

            # Add to patient's symptoms as well
            patient.symptoms.add(symptom_record.symptom)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='patients')
    def get_doctor_patients(self, request, pk=None):
        """Get patients for a specific doctor"""
        doctor = self.get_object()

        # Get distinct patients from disease cases
        patient_ids = DiseaseCase.objects.filter(
            doctor=doctor).values_list('patient', flat=True).distinct()
        patients = Patient.objects.filter(id__in=patient_ids)

        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='appointments')
    def get_doctor_appointments(self, request, pk=None):
        """Get appointments for a specific doctor"""
        doctor = self.get_object()

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

    @action(detail=True, methods=['get'], url_path='calendar-appointments')
    def get_calendar_appointments(self, request, pk=None):
        """Get appointments formatted for calendar display"""
        doctor = self.get_object()
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


class DiseaseCaseViewSet(viewsets.ModelViewSet):
    queryset = DiseaseCase.objects.all()
    serializer_class = DiseaseCaseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Get the doctor from the request user if not provided
        if 'doctor' not in self.request.data:
            try:
                doctor = self.request.user.doctor_profile
                serializer.save(doctor=doctor)
            except:
                # Handle case where user is not a doctor
                raise serializer.ValidationError(
                    "Doctor profile not found for current user")
        else:
            serializer.save()

        # Update patient status to diagnosed
        disease_case = serializer.instance
        patient = disease_case.patient
        patient.status = 'diagnosed'
        patient.save()


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Get the doctor from the request user if not provided
        if 'doctor' not in self.request.data:
            try:
                doctor = self.request.user.doctor_profile
                serializer.save(doctor=doctor)
            except:
                # Handle case where user is not a doctor
                raise serializer.ValidationError(
                    "Doctor profile not found for current user")
        else:
            serializer.save()


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
def api_disease_trends(request):
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_current_user_info(request):
    """API endpoint to get current user information"""
    user = request.user

    # Check if user is a doctor
    try:
        doctor = user.doctor_profile
        is_doctor = True
        doctor_data = DoctorSerializer(doctor).data
    except:
        is_doctor = False
        doctor_data = None

    response_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_doctor': is_doctor,
        'doctor_profile': doctor_data
    }

    return Response(response_data)

# dashboard/api_views.py
# Add this new endpoint function


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_past_statistics(request):
    """
    API endpoint to generate or update disease statistics for past periods
    Request Format:
    {
        "disease_type": "pneumonia",  # Optional, if not provided will update all diseases
        "start_date": "2024-01-01", 
        "end_date": "2025-04-27"  # Optional, defaults to current date
    }
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    try:
        # Parse request data
        data = request.data
        disease_type = data.get('disease_type', None)
        start_date_str = data.get('start_date', None)
        end_date_str = data.get('end_date', None)

        if not start_date_str:
            return Response({"error": "start_date is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(
            end_date_str, '%Y-%m-%d').date() if end_date_str else timezone.now().date()

        # Get disease if type provided
        disease = None
        if disease_type:
            try:
                disease = Disease.objects.get(type=disease_type)
            except Disease.DoesNotExist:
                return Response({"error": f"Disease with type '{disease_type}' not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Process each month in the range
        current_date = start_date
        months_processed = 0
        stats_created = []

        while current_date <= end_date:
            month = current_date.month
            year = current_date.year

            # Process either specific disease or all diseases
            diseases_to_process = [
                disease] if disease else Disease.objects.all()

            for disease_obj in diseases_to_process:
                # Count cases for this disease in this month/year
                cases = DiseaseCase.objects.filter(
                    disease=disease_obj,
                    diagnosis_date__month=month,
                    diagnosis_date__year=year
                )
                current_count = cases.count()

                # Get previous month for percent change calculation
                prev_month = 12 if month == 1 else month - 1
                prev_year = year - 1 if month == 1 else year

                try:
                    prev_stat = DiseaseStatistic.objects.get(
                        disease=disease_obj,
                        month=prev_month,
                        year=prev_year
                    )
                    prev_count = prev_stat.case_count
                    percent_change = ((current_count - prev_count) /
                                      prev_count * 100) if prev_count else 0
                except DiseaseStatistic.DoesNotExist:
                    percent_change = 0

                # Update or create statistics record
                stat, created = DiseaseStatistic.objects.update_or_create(
                    disease=disease_obj,
                    month=month,
                    year=year,
                    defaults={
                        'case_count': current_count,
                        'percent_change': round(percent_change, 2)
                    }
                )

                stats_created.append(f"{disease_obj.name} - {month}/{year}")

            months_processed += 1

            # Move to next month
            current_date = (
                current_date + relativedelta(months=1)).replace(day=1)

        # Return success response with details
        return Response({
            "success": True,
            "message": f"Statistics updated for {months_processed} months",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "disease": disease.name if disease else "All diseases",
            "periods_updated": len(stats_created),
            # Show first 10 entries as examples
            "sample_entries": stats_created[:10]
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
