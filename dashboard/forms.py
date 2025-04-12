from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Patient,
    Doctor,
    DiseaseCase,
    Appointment,
    Symptom,
    PatientSymptomRecord
)


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone', 'email', 'status',
            'diabetes', 'hypertension', 'asthma', 'allergies',
            'heart_disease', 'stroke', 'cancer', 'depression',
            'temperature', 'heart_rate', 'blood_pressure_systolic',
            'blood_pressure_diastolic', 'respiratory_rate', 'oxygen_saturation',
            'smoking_status', 'family_history', 'surgical_history',
            'prior_tb_exposure', 'previous_cardiac_conditions',
            'blood_glucose', 'cholesterol', 'hba1c',
            'white_blood_cell_count', 'c_reactive_protein', 'bnp',
            'additional_notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'additional_notes': forms.Textarea(attrs={'rows': 4}),
            'family_history': forms.Textarea(attrs={'rows': 3}),
            'surgical_history': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'blood_pressure_systolic': _('Blood Pressure (systolic)'),
            'blood_pressure_diastolic': _('Blood Pressure (diastolic)'),
            'hba1c': _('HbA1c (%)'),
            'blood_glucose': _('Blood Glucose (mg/dL)'),
            'cholesterol': _('Cholesterol (mg/dL)'),
            'white_blood_cell_count': _('White Blood Cell Count (×10^3/μL)'),
            'c_reactive_protein': _('C-Reactive Protein (mg/L)'),
            'bnp': _('BNP (pg/mL)'),
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['specialty', 'hospital', 'years_of_experience', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class DiseaseCaseForm(forms.ModelForm):
    class Meta:
        model = DiseaseCase
        fields = ['patient', 'disease', 'diagnosis_date',
                  'severity', 'notes', 'status']
        widgets = {
            'diagnosis_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            self.instance.doctor = doctor


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'disease_case', 'date',
                  'time', 'appointment_type', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)

        if doctor:
            self.instance.doctor = doctor
            # Filter disease cases by doctor's patients
            self.fields['disease_case'].queryset = DiseaseCase.objects.filter(
                doctor=doctor)

        # Dynamic disease case filtering based on selected patient
        self.fields['disease_case'].queryset = DiseaseCase.objects.none()

        if 'patient' in self.initial:
            patient_id = self.initial['patient'].id
            self.fields['disease_case'].queryset = DiseaseCase.objects.filter(
                patient_id=patient_id)

        if self.instance.pk and self.instance.patient:
            self.fields['disease_case'].queryset = DiseaseCase.objects.filter(
                patient=self.instance.patient)


class SymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = ['name', 'description', 'related_diseases']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PatientSymptomRecordForm(forms.ModelForm):
    class Meta:
        model = PatientSymptomRecord
        fields = ['symptom', 'severity', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
