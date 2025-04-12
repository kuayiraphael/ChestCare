from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .models import (
    Disease,
    Patient,
    Doctor,
    DiseaseCase,
    Appointment,
    DiseaseStatistic,
    Symptom,
    PatientSymptomRecord
)
from .forms import (
    PatientForm,
    DoctorForm,
    DiseaseCaseForm,
    AppointmentForm,
    SymptomForm,
    PatientSymptomRecordForm
)


@login_required
def dashboard_home(request):
    """Main dashboard view showing summary of patients, diseases, and appointments"""
    # Get disease statistics
    disease_stats = {}
    for disease_type in Disease.DISEASE_TYPES:
        disease_code = disease_type[0]
        disease = Disease.objects.filter(type=disease_code).first()
        if disease:
            # Get statistics for the current month
            current_month = datetime.now().month
            current_year = datetime.now().year

            # Get or create statistics for current month
            try:
                current_stats = DiseaseStatistic.objects.get(
                    disease=disease,
                    month=current_month,
                    year=current_year
                )
            except DiseaseStatistic.DoesNotExist:
                # If no statistics exist yet, count cases from disease cases
                case_count = DiseaseCase.objects.filter(
                    disease=disease,
                    diagnosis_date__month=current_month,
                    diagnosis_date__year=current_year
                ).count()

                # Calculate percent change if previous month exists
                previous_date = datetime.now() - relativedelta(months=1)
                previous_month = previous_date.month
                previous_year = previous_date.year

                previous_count = DiseaseCase.objects.filter(
                    disease=disease,
                    diagnosis_date__month=previous_month,
                    diagnosis_date__year=previous_year
                ).count()

                percent_change = 0
                if previous_count > 0:
                    percent_change = (
                        (case_count - previous_count) / previous_count) * 100

                current_stats = DiseaseStatistic.objects.create(
                    disease=disease,
                    month=current_month,
                    year=current_year,
                    case_count=case_count,
                    percent_change=percent_change
                )

            # Get trends data for chart (6 months)
            trends_data = []
            for i in range(5, -1, -1):
                month_date = datetime.now() - relativedelta(months=i)
                month = month_date.month
                year = month_date.year

                try:
                    stat = DiseaseStatistic.objects.get(
                        disease=disease,
                        month=month,
                        year=year
                    )
                    trends_data.append({
                        'month': month_date.strftime('%B'),
                        'count': stat.case_count
                    })
                except DiseaseStatistic.DoesNotExist:
                    trends_data.append({
                        'month': month_date.strftime('%B'),
                        'count': 0
                    })

            disease_stats[disease_code] = {
                'name': disease.name,
                'case_count': current_stats.case_count,
                'percent_change': current_stats.percent_change,
                'trends': trends_data,
                'info': {
                    'definition': disease.description,
                    'causes': disease.causes,
                    'symptoms': disease.symptoms,
                    'treatment': disease.treatment,
                    'clinical_notes': disease.clinical_notes
                }
            }

    # Get upcoming appointments for the current doctor
    doctor = Doctor.objects.get(user=request.user)
    today = datetime.now().date()
    appointments = Appointment.objects.filter(
        doctor=doctor,
        date__gte=today,
        status='scheduled'
    ).order_by('date', 'time')[:5]

    context = {
        'disease_stats': disease_stats,
        'upcoming_appointments': appointments,
        'doctor': doctor,
    }

    return render(request, 'dashboard/home.html', context)


@login_required
def disease_trends(request):
    """View for disease trend analysis"""
    # Get trends for all diseases over the past 6 months
    diseases = Disease.objects.all()
    trends_data = {}

    for disease in diseases:
        disease_data = []
        for i in range(5, -1, -1):
            month_date = datetime.now() - relativedelta(months=i)
            month = month_date.month
            year = month_date.year

            try:
                stat = DiseaseStatistic.objects.get(
                    disease=disease,
                    month=month,
                    year=year
                )
                count = stat.case_count
            except DiseaseStatistic.DoesNotExist:
                count = 0

            disease_data.append({
                'month': month_date.strftime('%B'),
                'count': count
            })

        trends_data[disease.type] = {
            'name': disease.name,
            'data': disease_data
        }

    context = {
        'trends_data': trends_data
    }

    return render(request, 'dashboard/disease_trends.html', context)


# Patient Views
@method_decorator(login_required, name='dispatch')
class PatientListView(ListView):
    model = Patient
    template_name = 'dashboard/patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by search query
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)

        # Filter by gender
        gender = self.request.GET.get('gender')
        if gender and gender != 'all':
            queryset = queryset.filter(gender=gender)

        # Filter by age range
        age_range = self.request.GET.get('age')
        if age_range and age_range != 'all':
            if age_range == 'under18':
                eighteen_years_ago = datetime.now().date() - timedelta(days=365*18)
                queryset = queryset.filter(
                    date_of_birth__gt=eighteen_years_ago)
            elif age_range == '18-40':
                eighteen_years_ago = datetime.now().date() - timedelta(days=365*18)
                forty_years_ago = datetime.now().date() - timedelta(days=365*40)
                queryset = queryset.filter(
                    date_of_birth__lte=eighteen_years_ago, date_of_birth__gt=forty_years_ago)
            elif age_range == '41-60':
                forty_years_ago = datetime.now().date() - timedelta(days=365*40)
                sixty_years_ago = datetime.now().date() - timedelta(days=365*60)
                queryset = queryset.filter(
                    date_of_birth__lte=forty_years_ago, date_of_birth__gt=sixty_years_ago)
            elif age_range == 'over60':
                sixty_years_ago = datetime.now().date() - timedelta(days=365*60)
                queryset = queryset.filter(date_of_birth__lte=sixty_years_ago)

        return queryset


@method_decorator(login_required, name='dispatch')
class PatientDetailView(DetailView):
    model = Patient
    template_name = 'dashboard/patients/patient_detail.html'
    context_object_name = 'patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object

        # Get disease cases
        context['disease_cases'] = DiseaseCase.objects.filter(
            patient=patient).order_by('-diagnosis_date')

        # Get upcoming appointments
        context['appointments'] = Appointment.objects.filter(
            patient=patient).order_by('-date', '-time')

        # Get symptom records
        context['symptom_records'] = PatientSymptomRecord.objects.filter(
            patient=patient).order_by('-recorded_date')

        return context


@method_decorator(login_required, name='dispatch')
class PatientCreateView(CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'dashboard/patients/patient_form.html'
    success_url = reverse_lazy('patient-list')

    def form_valid(self, form):
        messages.success(self.request, 'Patient record created successfully.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class PatientUpdateView(UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = 'dashboard/patients/patient_form.html'

    def get_success_url(self):
        return reverse_lazy('patient-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Patient record updated successfully.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class PatientDeleteView(DeleteView):
    model = Patient
    template_name = 'dashboard/patients/patient_confirm_delete.html'
    success_url = reverse_lazy('patient-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Patient record deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Disease Case Views
@method_decorator(login_required, name='dispatch')
class DiseaseCaseCreateView(CreateView):
    model = DiseaseCase
    form_class = DiseaseCaseForm
    template_name = 'dashboard/cases/case_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Add current doctor to form
        kwargs['doctor'] = Doctor.objects.get(user=self.request.user)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill patient if provided in URL
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            initial['patient'] = Patient.objects.get(pk=patient_id)
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        # Update patient status
        patient = form.instance.patient
        patient.status = 'diagnosed'
        patient.save()

        messages.success(self.request, 'Disease case created successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('patient-detail', kwargs={'pk': self.object.patient.pk})


# Appointment Views
@method_decorator(login_required, name='dispatch')
class AppointmentListView(ListView):
    model = Appointment
    template_name = 'dashboard/appointments/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        # Get appointments for the current doctor
        doctor = Doctor.objects.get(user=self.request.user)
        queryset = Appointment.objects.filter(doctor=doctor)

        # Filter by date range
        date_filter = self.request.GET.get('date_filter', 'upcoming')
        today = datetime.now().date()

        if date_filter == 'upcoming':
            queryset = queryset.filter(date__gte=today)
        elif date_filter == 'past':
            queryset = queryset.filter(date__lt=today)
        elif date_filter == 'today':
            queryset = queryset.filter(date=today)
        elif date_filter == 'week':
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            queryset = queryset.filter(
                date__gte=week_start, date__lte=week_end)

        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('date', 'time')


@method_decorator(login_required, name='dispatch')
class AppointmentCreateView(CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'dashboard/appointments/appointment_form.html'
    success_url = reverse_lazy('appointment-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Add current doctor to form
        kwargs['doctor'] = Doctor.objects.get(user=self.request.user)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill patient if provided in URL
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            initial['patient'] = Patient.objects.get(pk=patient_id)
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Appointment scheduled successfully.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class AppointmentUpdateView(UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'dashboard/appointments/appointment_form.html'
    success_url = reverse_lazy('appointment-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Add current doctor to form
        kwargs['doctor'] = Doctor.objects.get(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Appointment updated successfully.')
        return super().form_valid(form)


# Symptom Views
@method_decorator(login_required, name='dispatch')
class SymptomListView(ListView):
    model = Symptom
    template_name = 'dashboard/symptoms/symptom_list.html'
    context_object_name = 'symptoms'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Symptom.objects.filter(name__icontains=query)
        return Symptom.objects.all()


@method_decorator(login_required, name='dispatch')
class SymptomCreateView(CreateView):
    model = Symptom
    form_class = SymptomForm
    template_name = 'dashboard/symptoms/symptom_form.html'
    success_url = reverse_lazy('symptom-list')


# API Views for AJAX requests
@login_required
def get_disease_data(request, disease_type):
    """API endpoint to get disease data for charts"""
    disease = get_object_or_404(Disease, type=disease_type)

    # Get monthly statistics for the past 12 months
    data = []
    for i in range(11, -1, -1):
        month_date = datetime.now() - relativedelta(months=i)
        month = month_date.month
        year = month_date.year

        try:
            stat = DiseaseStatistic.objects.get(
                disease=disease,
                month=month,
                year=year
            )
            count = stat.case_count
        except DiseaseStatistic.DoesNotExist:
            count = 0

        data.append({
            'month': month_date.strftime('%B'),
            'count': count
        })

    return JsonResponse({
        'name': disease.name,
        'data': data
    })


@login_required
def calendar_appointments(request):
    """API endpoint to get appointments for calendar view"""
    doctor = Doctor.objects.get(user=request.user)
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    # Convert to datetime objects
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        appointments = Appointment.objects.filter(
            doctor=doctor,
            date__gte=start_date,
            date__lte=end_date
        )
    else:
        appointments = Appointment.objects.filter(doctor=doctor)

    events = []
    for appointment in appointments:
        color = '#3788d8'  # default color
        if appointment.appointment_type == 'emergency':
            color = '#dc3545'  # red
        elif appointment.appointment_type == 'followup':
            color = '#28a745'  # green

        events.append({
            'id': appointment.id,
            'title': f"{appointment.patient} - {appointment.get_appointment_type_display()}",
            'start': f"{appointment.date.isoformat()}T{appointment.time.isoformat()}",
            'url': reverse_lazy('appointment-update', kwargs={'pk': appointment.pk}),
            'backgroundColor': color,
            'borderColor': color
        })

    return JsonResponse(events, safe=False)


@login_required
def patient_symptom_record_add(request, patient_id):
    """View to add symptom records for a patient"""
    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == 'POST':
        form = PatientSymptomRecordForm(request.POST)
        if form.is_valid():
            symptom_record = form.save(commit=False)
            symptom_record.patient = patient
            symptom_record.save()
            messages.success(request, 'Symptom record added successfully.')
            return redirect('patient-detail', pk=patient_id)
    else:
        form = PatientSymptomRecordForm()

    context = {
        'form': form,
        'patient': patient
    }

    return render(request, 'dashboard/symptoms/symptom_record_form.html', context)
