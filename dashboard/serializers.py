# dashboard/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
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

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = '__all__'


class SymptomSerializer(serializers.ModelSerializer):
    related_diseases_detail = DiseaseSerializer(
        source='related_diseases', many=True, read_only=True)

    class Meta:
        model = Symptom
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    # Existing computed fields
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    # New created_by fields
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_gender_display(self, obj):
        return obj.get_gender_display()

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_age(self, obj):
        from datetime import date
        today = date.today()
        born = obj.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class DoctorSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    full_name = serializers.SerializerMethodField()
    patient_count = serializers.ReadOnlyField()
    total_diagnoses = serializers.ReadOnlyField()

    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    country = serializers.CharField(source='user.country', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'user_details', 'full_name', 'specialty', 'hospital',
            'years_of_experience', 'bio', 'avatar_url', 'languages',
            'license_number', 'consultation_fee', 'working_hours_start',
            'working_hours_end', 'is_available', 'patient_count',
            'total_diagnoses', 'email', 'phone', 'country',
            'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"


# serializer for profile updates
class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating doctor profile information"""

    # User fields
    first_name = serializers.CharField(
        source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    phone_number = serializers.CharField(
        source='user.phone_number', required=False)
    country = serializers.CharField(source='user.country', required=False)

    class Meta:
        model = Doctor
        fields = [
            'specialty', 'hospital', 'years_of_experience', 'bio',
            'languages', 'license_number', 'consultation_fee',
            'working_hours_start', 'working_hours_end', 'is_available',
            'first_name', 'last_name', 'email', 'phone_number', 'country'
        ]

    def update(self, instance, validated_data):
        # Handle user fields
        user_data = {}
        user_fields = ['first_name', 'last_name',
                       'email', 'phone_number', 'country']

        for field in user_fields:
            if f'user.{field}' in validated_data:
                user_data[field] = validated_data.pop(f'user.{field}')

        # Update user fields
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save()

        # Update doctor fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        return instance


# serializer for dashboard statistics
class DoctorDashboardStatsSerializer(serializers.Serializer):
    """Serializer for doctor dashboard statistics"""
    total_patients = serializers.IntegerField()
    total_diagnoses = serializers.IntegerField()
    todays_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()
    avg_response_time = serializers.CharField()
    accuracy_rate = serializers.CharField()


# serializer for recent activity
class DoctorActivitySerializer(serializers.Serializer):
    """Serializer for doctor recent activity"""
    type = serializers.CharField()
    date = serializers.DateField()
    time = serializers.TimeField(required=False)
    patient_name = serializers.CharField()
    status = serializers.CharField(required=False)
    appointment_type = serializers.CharField(required=False)
    disease = serializers.CharField(required=False)
    severity = serializers.CharField(required=False)

class DiseaseCaseSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    disease_detail = DiseaseSerializer(source='disease', read_only=True)
    doctor_detail = DoctorSerializer(source='doctor', read_only=True)
    severity_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = DiseaseCase
        fields = '__all__'

    def get_severity_display(self, obj):
        return dict(DiseaseCase._meta.get_field('severity').choices).get(obj.severity)

    def get_status_display(self, obj):
        return dict(DiseaseCase._meta.get_field('status').choices).get(obj.status)


class AppointmentSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    doctor_detail = DoctorSerializer(source='doctor', read_only=True)
    disease_case_detail = DiseaseCaseSerializer(
        source='disease_case', read_only=True)
    appointment_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'

    def get_appointment_type_display(self, obj):
        return dict(Appointment._meta.get_field('appointment_type').choices).get(obj.appointment_type)

    def get_status_display(self, obj):
        return dict(Appointment._meta.get_field('status').choices).get(obj.status)


class PatientSymptomRecordSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    symptom_detail = SymptomSerializer(source='symptom', read_only=True)
    severity_display = serializers.SerializerMethodField()

    class Meta:
        model = PatientSymptomRecord
        fields = '__all__'

    def get_severity_display(self, obj):
        return dict(PatientSymptomRecord._meta.get_field('severity').choices).get(obj.severity)


class DiseaseStatisticSerializer(serializers.ModelSerializer):
    disease_detail = DiseaseSerializer(source='disease', read_only=True)

    class Meta:
        model = DiseaseStatistic
        fields = '__all__'
