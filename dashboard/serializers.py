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
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'

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

    class Meta:
        model = Doctor
        fields = '__all__'

    def get_full_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"


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
