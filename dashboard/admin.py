from django.contrib import admin
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


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    search_fields = ('name', 'type')


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('related_diseases',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name',
                    'gender', 'date_of_birth', 'status')
    list_filter = ('gender', 'status', 'diabetes', 'hypertension', 'asthma')
    search_fields = ('first_name', 'last_name', 'email')
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'email', 'status')
        }),
        ('Medical History', {
            'fields': ('diabetes', 'hypertension', 'asthma', 'allergies', 'heart_disease',
                       'stroke', 'cancer', 'depression', 'prior_tb_exposure', 'previous_cardiac_conditions')
        }),
        ('Vital Signs', {
            'fields': ('temperature', 'heart_rate', 'blood_pressure_systolic',
                       'blood_pressure_diastolic', 'respiratory_rate', 'oxygen_saturation')
        }),
        ('Laboratory Results', {
            'fields': ('blood_glucose', 'cholesterol', 'hba1c',
                       'white_blood_cell_count', 'c_reactive_protein', 'bnp')
        }),
        ('Additional Information', {
            'fields': ('smoking_status', 'family_history', 'surgical_history', 'additional_notes')
        }),
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'hospital', 'years_of_experience')
    search_fields = ('user__first_name', 'user__last_name',
                     'specialty', 'hospital')


@admin.register(DiseaseCase)
class DiseaseCaseAdmin(admin.ModelAdmin):
    list_display = ('patient', 'disease', 'doctor',
                    'diagnosis_date', 'severity', 'status')
    list_filter = ('status', 'severity', 'diagnosis_date')
    search_fields = ('patient__first_name',
                     'patient__last_name', 'disease__name')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time',
                    'appointment_type', 'status')
    list_filter = ('status', 'appointment_type', 'date')
    search_fields = ('patient__first_name',
                     'patient__last_name', 'doctor__user__last_name')


@admin.register(PatientSymptomRecord)
class PatientSymptomRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'symptom', 'severity', 'recorded_date')
    list_filter = ('severity', 'recorded_date')
    search_fields = ('patient__first_name',
                     'patient__last_name', 'symptom__name')


@admin.register(DiseaseStatistic)
class DiseaseStatisticAdmin(admin.ModelAdmin):
    list_display = ('disease', 'month', 'year', 'case_count', 'percent_change')
    list_filter = ('disease', 'year', 'month')
