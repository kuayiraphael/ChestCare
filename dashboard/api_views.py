# dashboard/api_views.py
import cloudinary
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
from datetime import datetime, timedelta,time


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

    def perform_create(self, serializer):
        """Automatically set the created_by field to current user when creating a patient"""
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        """Custom update method with better error handling"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Log the incoming data for debugging
        print(f"Updating patient {instance.id} with data: {request.data}")

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)

        if serializer.is_valid():
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        else:
            # Log validation errors for debugging
            print(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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

    @action(detail=False, methods=['get'], url_path='profile')
    def get_current_doctor_profile(self, request):
        """Get current logged-in doctor's profile"""
        try:
            doctor = request.user.doctor_profile
            serializer = self.get_serializer(doctor)

            # Add user information
            profile_data = serializer.data
            profile_data['user_info'] = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
                'country': request.user.country,
            }

            return Response(profile_data)
        except Exception as e:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch'], url_path='update-profile')
    def update_current_doctor_profile(self, request):
        """Update current logged-in doctor's profile"""
        try:
            doctor = request.user.doctor_profile
            user = request.user

            # Update user fields
            user_fields = ['first_name', 'last_name',
                           'email', 'phone_number', 'country']
            for field in user_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            user.save()

            # Update doctor fields
            doctor_fields = ['specialty', 'hospital',
                             'years_of_experience', 'bio']
            for field in doctor_fields:
                if field in request.data:
                    setattr(doctor, field, request.data[field])
            doctor.save()

            # Return updated profile
            serializer = self.get_serializer(doctor)
            profile_data = serializer.data
            profile_data['user_info'] = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'country': user.country,
            }

            return Response({
                'message': 'Profile updated successfully',
                'profile': profile_data
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to update profile: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='upload-avatar')
    def upload_avatar(self, request):
        """Upload doctor's profile avatar to Cloudinary"""
        try:
            if 'avatar' not in request.FILES:
                return Response(
                    {'error': 'No avatar file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            avatar_file = request.FILES['avatar']

            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                avatar_file,
                folder="chestcare/doctor_avatars/",
                public_id=f"doctor_{request.user.id}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {'width': 200, 'height': 200, 'crop': 'fill', 'gravity': 'face'}
                ]
            )

            # Save the URL to doctor profile (you'll need to add this field to Doctor model)
            doctor = request.user.doctor_profile
            doctor.avatar_url = upload_result['secure_url']
            doctor.save()

            return Response({
                'message': 'Avatar uploaded successfully',
                'avatar_url': upload_result['secure_url']
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to upload avatar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def get_dashboard_stats(self, request):
        """Get doctor's dashboard statistics"""
        try:
            doctor = request.user.doctor_profile

            # Total patients (unique patients the doctor has treated)
            total_patients = DiseaseCase.objects.filter(
                doctor=doctor
            ).values('patient').distinct().count()

            # Total diagnoses made
            total_diagnoses = DiseaseCase.objects.filter(doctor=doctor).count()

            # Today's appointments
            today = timezone.now().date()
            todays_appointments = Appointment.objects.filter(
                doctor=doctor,
                date=today,
                status__in=['scheduled', 'rescheduled']
            ).count()

            # Upcoming appointments (next 7 days)
            end_date = today + timedelta(days=7)
            upcoming_appointments = Appointment.objects.filter(
                doctor=doctor,
                date__gt=today,
                date__lte=end_date,
                status__in=['scheduled', 'rescheduled']
            ).count()

            # Average response time (mock calculation - you can implement actual logic)
            # This could be based on appointment creation to completion time
            avg_response_hours = 2.4  # You'll need to implement actual calculation

            # Accuracy rate (mock - you can implement based on successful diagnoses)
            accuracy_rate = 94.3  # You'll need to implement actual calculation

            return Response({
                'total_patients': total_patients,
                'total_diagnoses': total_diagnoses,
                'todays_appointments': todays_appointments,
                'upcoming_appointments': upcoming_appointments,
                'avg_response_time': f"{avg_response_hours} hours",
                'accuracy_rate': f"{accuracy_rate}%"
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to fetch dashboard stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='recent-activity')
    def get_recent_activity(self, request):
        """Get doctor's recent activity"""
        try:
            doctor = request.user.doctor_profile
            limit = int(request.query_params.get('limit', 10))

            # Recent appointments
            recent_appointments = Appointment.objects.filter(
                doctor=doctor
            ).order_by('-date', '-time')[:limit]

            # Recent diagnoses
            recent_diagnoses = DiseaseCase.objects.filter(
                doctor=doctor
            ).order_by('-diagnosis_date')[:limit]

            # Format the activity feed
            activity_feed = []

            for appointment in recent_appointments:
                activity_feed.append({
                    'type': 'appointment',
                    'date': appointment.date,
                    'time': appointment.time,
                    'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}",
                    'status': appointment.status,
                    'appointment_type': appointment.get_appointment_type_display()
                })

            for diagnosis in recent_diagnoses:
                activity_feed.append({
                    'type': 'diagnosis',
                    'date': diagnosis.diagnosis_date,
                    'patient_name': f"{diagnosis.patient.first_name} {diagnosis.patient.last_name}",
                    'disease': diagnosis.disease.name,
                    'severity': diagnosis.get_severity_display()
                })

            # Sort by date (most recent first)
            activity_feed.sort(key=lambda x: x['date'], reverse=True)

            return Response(activity_feed[:limit])

        except Exception as e:
            return Response(
                {'error': f'Failed to fetch recent activity: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='specialization-stats')
    def get_specialization_stats(self, request):
        """Get statistics related to doctor's specialization"""
        try:
            doctor = request.user.doctor_profile

            # Disease breakdown for this doctor
            disease_stats = DiseaseCase.objects.filter(doctor=doctor).values(
                'disease__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            # Monthly case trends (last 12 months)
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=365)

            monthly_cases = []
            current_date = start_date.replace(
                day=1)  # Start from first of month

            while current_date <= end_date:
                cases_count = DiseaseCase.objects.filter(
                    doctor=doctor,
                    diagnosis_date__year=current_date.year,
                    diagnosis_date__month=current_date.month
                ).count()

                monthly_cases.append({
                    'month': current_date.strftime('%B %Y'),
                    'count': cases_count
                })

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(
                        month=current_date.month + 1)

            return Response({
                'disease_breakdown': list(disease_stats),
                'monthly_trends': monthly_cases
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to fetch specialization stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




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

    def get_queryset(self):
        """Filter appointments based on user role and query parameters"""
        queryset = Appointment.objects.all()

        # If user is a doctor, filter to their appointments only
        try:
            doctor = self.request.user.doctor_profile
            queryset = queryset.filter(doctor=doctor)
        except:
            pass  # User is not a doctor, show all appointments (for admin)

        # Apply additional filters
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=date_from)
            except ValueError:
                pass

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=date_to)
            except ValueError:
                pass

        return queryset.order_by('date', 'time')

    def perform_create(self, serializer):
        """Automatically set the doctor when creating appointment"""
        if 'doctor' not in self.request.data:
            try:
                doctor = self.request.user.doctor_profile
                serializer.save(doctor=doctor)
            except:
                raise serializer.ValidationError(
                    "Doctor profile not found for current user")
        else:
            serializer.save()

    def update(self, request, *args, **kwargs):
        """Enhanced update with validation and logging"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check if appointment can be updated (not in past or already completed)
        if instance.date < timezone.now().date():
            return Response(
                {'error': 'Cannot update past appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if instance.status == 'completed':
            return Response(
                {'error': 'Cannot update completed appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)

        if serializer.is_valid():
            # If status is being changed to 'rescheduled', validate new date/time
            if request.data.get('status') == 'rescheduled':
                new_date = request.data.get('date', instance.date)
                new_time = request.data.get('time', instance.time)

                # Ensure new appointment is in the future
                if isinstance(new_date, str):
                    new_date = datetime.strptime(new_date, '%Y-%m-%d').date()
                if isinstance(new_time, str):
                    new_time = datetime.strptime(new_time, '%H:%M:%S').time()

                new_datetime = datetime.combine(new_date, new_time)
                if new_datetime <= timezone.now():
                    return Response(
                        {'error': 'Rescheduled appointment must be in the future'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            self.perform_update(serializer)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Enhanced delete with business logic validation"""
        instance = self.get_object()

        # Check if appointment can be deleted
        if instance.status == 'completed':
            return Response(
                {'error': 'Cannot delete completed appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If appointment is today or in the past, require cancellation instead
        if instance.date <= timezone.now().date():
            return Response(
                {'error': 'Cannot delete appointments for today or past dates. Please cancel instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform the deletion
        appointment_info = f"{instance.patient.full_name} - {instance.date} {instance.time}"
        self.perform_destroy(instance)

        return Response(
            {'message': f'Appointment deleted successfully: {appointment_info}'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_appointment(self, request, pk=None):
        """Cancel a specific appointment"""
        appointment = self.get_object()

        if appointment.status == 'completed':
            return Response(
                {'error': 'Cannot cancel completed appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'cancelled'
        appointment.notes = request.data.get('notes', appointment.notes)
        appointment.save()

        serializer = self.get_serializer(appointment)
        return Response({
            'message': 'Appointment cancelled successfully',
            'appointment': serializer.data
        })

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete_appointment(self, request, pk=None):
        """Mark appointment as completed with notes"""
        appointment = self.get_object()

        if appointment.status == 'cancelled':
            return Response(
                {'error': 'Cannot complete cancelled appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'completed'
        appointment.notes = request.data.get('notes', appointment.notes)
        appointment.save()

        serializer = self.get_serializer(appointment)
        return Response({
            'message': 'Appointment marked as completed',
            'appointment': serializer.data
        })

    @action(detail=True, methods=['patch'], url_path='reschedule')
    def reschedule_appointment(self, request, pk=None):
        """Reschedule an appointment to a new date/time"""
        appointment = self.get_object()

        if appointment.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot reschedule {appointment.status} appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_date = request.data.get('date')
        new_time = request.data.get('time')

        if not new_date or not new_time:
            return Response(
                {'error': 'Both date and time are required for rescheduling'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- parsing helpers ---
        def parse_date(value):
            if hasattr(value, 'year'):  # already a date/datetime object
                return value.date() if hasattr(value, 'date') else value
            # try common formats
            for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except Exception:
                    continue
            # try ISO parse fallback
            try:
                return datetime.fromisoformat(value).date()
            except Exception:
                raise ValueError("Invalid date format")

        def parse_time(value):
            if hasattr(value, 'hour'):  # already time/datetime object
                return value.time() if hasattr(value, 'time') else value
            # try common formats
            for fmt in ('%H:%M:%S', '%H:%M'):
                try:
                    return datetime.strptime(value, fmt).time()
                except Exception:
                    continue
            # try ISO parse fallback
            try:
                parsed = datetime.fromisoformat(value)
                return parsed.time()
            except Exception:
                raise ValueError("Invalid time format")

        # --- parse and combine ---
        try:
            new_date = parse_date(new_date)
            new_time = parse_time(new_time)
        except ValueError:
            return Response(
                {'error': 'Invalid date or time format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_datetime = datetime.combine(new_date, new_time)

        # Make new_datetime timezone-aware using current Django timezone (fixes naive vs aware)
        try:
            if timezone.is_naive(new_datetime):
                tz = timezone.get_current_timezone()
                new_datetime = timezone.make_aware(new_datetime, tz)
        except Exception as e:
            # Defensive fallback
            return Response(
                {'error': f'Failed to interpret new datetime: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure new datetime is in the future compared to timezone-aware now()
        if new_datetime <= timezone.now():
            return Response(
                {'error': 'New appointment time must be in the future'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for conflicts (compare date/time fields as before)
        conflicts = Appointment.objects.filter(
            doctor=appointment.doctor,
            date=new_date,
            time=new_time,
            status__in=['scheduled', 'rescheduled']
        ).exclude(pk=appointment.pk)

        if conflicts.exists():
            return Response(
                {'error': 'Time slot already booked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update appointment
        appointment.date = new_date
        appointment.time = new_time
        appointment.status = 'rescheduled'
        appointment.notes = request.data.get('notes', appointment.notes)
        appointment.save()

        serializer = self.get_serializer(appointment)
        return Response({
            'message': 'Appointment rescheduled successfully',
            'appointment': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_appointments(self, request):
        """Get upcoming appointments for the doctor"""
        try:
            doctor = request.user.doctor_profile
            days_ahead = int(request.query_params.get('days', 7))

            end_date = timezone.now().date() + timedelta(days=days_ahead)
            appointments = Appointment.objects.filter(
                doctor=doctor,
                date__gte=timezone.now().date(),
                date__lte=end_date,
                status__in=['scheduled', 'rescheduled']
            ).order_by('date', 'time')

            serializer = self.get_serializer(appointments, many=True)
            return Response(serializer.data)

        except:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='today')
    def today_appointments(self, request):
        """Get today's appointments for the doctor"""
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()

            appointments = Appointment.objects.filter(
                doctor=doctor,
                date=today
            ).order_by('time')

            serializer = self.get_serializer(appointments, many=True)
            return Response(serializer.data)

        except:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        """Get available time slots for a specific date"""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'Date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = request.user.doctor_profile
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Check if date is in the past
            if appointment_date < timezone.now().date():
                return Response(
                    {'error': 'Cannot check availability for past dates'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Define working hours (can be customized)
            working_hours_start = time(9, 0)  # 9:00 AM
            working_hours_end = time(17, 0)   # 5:00 PM
            slot_duration = 30  # 30 minutes per slot

            # Get existing appointments for the date
            existing_appointments = Appointment.objects.filter(
                doctor=doctor,
                date=appointment_date,
                status__in=['scheduled', 'rescheduled']
            ).values_list('time', flat=True)

            # Generate available slots
            available_slots = []
            current_time = working_hours_start

            while current_time < working_hours_end:
                if current_time not in existing_appointments:
                    available_slots.append(current_time.strftime('%H:%M:%S'))

                # Add slot duration
                current_datetime = datetime.combine(
                    appointment_date, current_time)
                current_datetime += timedelta(minutes=slot_duration)
                current_time = current_datetime.time()

            return Response({
                'date': date_str,
                'available_slots': available_slots
            })

        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='statistics')
    def appointment_statistics(self, request):
        """Get appointment statistics for the doctor"""
        try:
            doctor = request.user.doctor_profile

            # Get date range
            days = int(request.query_params.get('days', 30))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)

            appointments = Appointment.objects.filter(
                doctor=doctor,
                date__gte=start_date,
                date__lte=end_date
            )

            # Count by status
            stats = {
                'total': appointments.count(),
                'scheduled': appointments.filter(status='scheduled').count(),
                'completed': appointments.filter(status='completed').count(),
                'cancelled': appointments.filter(status='cancelled').count(),
                'rescheduled': appointments.filter(status='rescheduled').count(),
            }

            # Count by type
            type_stats = {}
            for type_choice in Appointment._meta.get_field('appointment_type').choices:
                type_code, type_name = type_choice
                count = appointments.filter(appointment_type=type_code).count()
                type_stats[type_code] = {
                    'name': type_name,
                    'count': count
                }

            return Response({
                'period': f'{start_date} to {end_date}',
                'status_breakdown': stats,
                'type_breakdown': type_stats
            })

        except:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

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
