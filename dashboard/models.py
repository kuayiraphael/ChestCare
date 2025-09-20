# dashboard/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Disease(models.Model):
    """Model for tracking different pulmonary diseases"""
    DISEASE_TYPES = (
        ('cardiomegaly', 'Cardiomegaly'),
        ('pneumonia', 'Pneumonia'),
        ('tuberculosis', 'Tuberculosis'),
        ('pulmonary', 'Pulmonary Hypertension'),
    )

    name = models.CharField(_('disease name'), max_length=100)
    type = models.CharField(
        _('disease type'), max_length=50, choices=DISEASE_TYPES)
    description = models.TextField(_('description'))
    causes = models.TextField(_('causes'))
    symptoms = models.TextField(_('symptoms'))
    treatment = models.TextField(_('treatment'))
    clinical_notes = models.TextField(_('clinical notes'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Disease')
        verbose_name_plural = _('Diseases')


class Symptom(models.Model):
    """Model for tracking individual symptoms"""
    name = models.CharField(_('symptom name'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)
    related_diseases = models.ManyToManyField(
        Disease, related_name='related_symptoms', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Symptom')
        verbose_name_plural = _('Symptoms')


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    STATUS_CHOICES = [
        ('diagnosed', 'Diagnosed'),
        ('undiagnosed', 'Undiagnosed'),
        ('recovered', 'Recovered'),
        ('deceased', 'Deceased'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    xray_image_url = models.URLField(
        blank=True, null=True, help_text="Cloudinary URL for chest X-ray image")

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='undiagnosed')

    # Patient symptoms - many-to-many relationship with Symptom model
    symptoms = models.ManyToManyField(
        Symptom, related_name='patients', blank=True)

    # Clinical Information
    diabetes = models.BooleanField(default=False)
    hypertension = models.BooleanField(default=False)
    asthma = models.BooleanField(default=False)
    allergies = models.BooleanField(default=False)
    heart_disease = models.BooleanField(default=False)
    stroke = models.BooleanField(default=False)
    cancer = models.BooleanField(default=False)
    depression = models.BooleanField(default=False)

    # Vital Signs
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                      validators=[MinValueValidator(30), MaxValueValidator(45)])
    heart_rate = models.IntegerField(blank=True, null=True,
                                     validators=[MinValueValidator(0), MaxValueValidator(300)])
    blood_pressure_systolic = models.IntegerField(blank=True, null=True,
                                                  validators=[MinValueValidator(0), MaxValueValidator(300)])
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True,
                                                   validators=[MinValueValidator(0), MaxValueValidator(300)])
    respiratory_rate = models.IntegerField(blank=True, null=True,
                                           validators=[MinValueValidator(0), MaxValueValidator(100)])
    oxygen_saturation = models.IntegerField(blank=True, null=True,
                                            validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Medical History
    smoking_status = models.CharField(max_length=100, blank=True)
    family_history = models.TextField(blank=True)
    surgical_history = models.TextField(blank=True)
    prior_tb_exposure = models.BooleanField(default=False)
    previous_cardiac_conditions = models.BooleanField(default=False)

    # Laboratory Results
    blood_glucose = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    cholesterol = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    hba1c = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    white_blood_cell_count = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    c_reactive_protein = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    bnp = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)

    # Additional Notes
    additional_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='created_patients',
        help_text="Doctor who created this patient record"
    )
    profile_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Cloudinary URL for patient profile image"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-created_at']


class PatientSymptomRecord(models.Model):
    """Model for tracking symptom severity and notes for patients"""
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='symptom_records')
    symptom = models.ForeignKey(
        Symptom, on_delete=models.CASCADE, related_name='patient_records')
    severity = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ], default='moderate')
    notes = models.TextField(blank=True, null=True)
    recorded_date = models.DateField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.patient} - {self.symptom} ({self.severity})"

    class Meta:
        verbose_name = _('Patient Symptom Record')
        verbose_name_plural = _('Patient Symptom Records')


class Doctor(models.Model):
    """Model for doctor details (extends User model)"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(
        _('specialty'), max_length=100, blank=True, null=True)
    hospital = models.CharField(
        _('hospital'), max_length=150, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(
        _('years of experience'), default=0)
    bio = models.TextField(_('bio'), blank=True, null=True)

    # Add these new fields
    avatar_url = models.URLField(
        _('avatar URL'),
        blank=True,
        null=True,
        help_text="Cloudinary URL for doctor's profile picture"
    )
    languages = models.JSONField(
        _('languages spoken'),
        default=list,
        blank=True,
        help_text="List of languages the doctor speaks"
    )
    license_number = models.CharField(
        _('medical license number'),
        max_length=50,
        blank=True,
        null=True
    )
    consultation_fee = models.DecimalField(
        _('consultation fee'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    working_hours_start = models.TimeField(
        _('working hours start'),
        default='09:00'
    )
    working_hours_end = models.TimeField(
        _('working hours end'),
        default='17:00'
    )
    is_available = models.BooleanField(
        _('is available for appointments'),
        default=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    @property
    def full_name(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    @property
    def patient_count(self):
        """Get total unique patients treated by this doctor"""
        return DiseaseCase.objects.filter(
            doctor=self
        ).values('patient').distinct().count()

    @property
    def total_diagnoses(self):
        """Get total diagnoses made by this doctor"""
        return DiseaseCase.objects.filter(doctor=self).count()

    class Meta:
        verbose_name = _('Doctor')
        verbose_name_plural = _('Doctors')
        ordering = ['-created_at']

        
class DiseaseCase(models.Model):
    """Model for tracking disease cases"""
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='disease_cases')
    disease = models.ForeignKey(
        Disease, on_delete=models.CASCADE, related_name='cases')
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name='handled_cases')
    diagnosis_date = models.DateField(_('diagnosis date'))
    severity = models.CharField(_('severity'), max_length=50, choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ])
    notes = models.TextField(_('notes'), blank=True, null=True)
    status = models.CharField(_('status'), max_length=50, choices=[
        ('active', 'Active'),
        ('recovered', 'Recovered'),
        ('worsened', 'Worsened'),
        ('deceased', 'Deceased'),
    ], default='active')

    def __str__(self):
        return f"{self.disease.name} - {self.patient}"

    class Meta:
        verbose_name = _('Disease Case')
        verbose_name_plural = _('Disease Cases')


class Appointment(models.Model):
    """Model for doctor appointments"""
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name='appointments')
    disease_case = models.ForeignKey(
        DiseaseCase, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    date = models.DateField(_('appointment date'))
    time = models.TimeField(_('appointment time'))
    appointment_type = models.CharField(
        _('appointment type'),
        max_length=100,
        choices=[
            ('consultation', 'Consultation'),
            ('follow_up', 'Follow Up'),
            ('checkup', 'Check Up'),
            ('emergency', 'Emergency'),
            ('screening', 'Screening'),
        ]
    )

    status = models.CharField(_('status'), max_length=50, choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ], default='scheduled')
    notes = models.TextField(_('notes'), blank=True, null=True)

    def __str__(self):
        return f"{self.patient} - {self.date} {self.time}"

    class Meta:
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')


class DiseaseStatistic(models.Model):
    """Model for disease statistics by month"""
    disease = models.ForeignKey(
        Disease, on_delete=models.CASCADE, related_name='statistics')
    month = models.PositiveIntegerField(_('month'))  # 1-12
    year = models.PositiveIntegerField(_('year'))
    case_count = models.PositiveIntegerField(_('case count'))
    percent_change = models.FloatField(
        _('percent change'), default=0.0)  # From previous month

    def __str__(self):
        return f"{self.disease.name} - {self.month}/{self.year}"

    class Meta:
        verbose_name = _('Disease Statistic')
        verbose_name_plural = _('Disease Statistics')
        unique_together = ('disease', 'month', 'year')
