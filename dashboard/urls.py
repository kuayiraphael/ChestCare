# dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

# Create a router for REST API
router = DefaultRouter()
router.register('diseases', api_views.DiseaseViewSet)
router.register('patients', api_views.PatientViewSet)
router.register('doctors', api_views.DoctorViewSet)
router.register('cases', api_views.DiseaseCaseViewSet)
router.register('appointments', api_views.AppointmentViewSet)
router.register('symptoms', api_views.SymptomViewSet)
router.register('symptom-records', api_views.PatientSymptomRecordViewSet)

urlpatterns = [
    # API endpoints for Postman testing
    path('api/', include(router.urls)),
    path('api/dashboard-summary/', api_views.api_dashboard_summary,
         name='api-dashboard-summary'),

    # Original dashboard URLs (keep these for web UI)
    path('', views.dashboard_home, name='dashboard-home'),
    path('disease-trends/', views.disease_trends, name='disease-trends'),

    # Patient URLs
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/create/', views.PatientCreateView.as_view(),
         name='patient-create'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(),
         name='patient-detail'),
    path('patients/<int:pk>/update/',
         views.PatientUpdateView.as_view(), name='patient-update'),
    path('patients/<int:pk>/delete/',
         views.PatientDeleteView.as_view(), name='patient-delete'),

    # Disease Case URLs
    path('cases/create/', views.DiseaseCaseCreateView.as_view(), name='case-create'),
    path('cases/create/<int:patient_id>/',
         views.DiseaseCaseCreateView.as_view(), name='case-create-for-patient'),

    # Appointment URLs
    path('appointments/', views.AppointmentListView.as_view(),
         name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(),
         name='appointment-create'),
    path('appointments/create/<int:patient_id>/',
         views.AppointmentCreateView.as_view(), name='appointment-create-for-patient'),
    path('appointments/<int:pk>/update/',
         views.AppointmentUpdateView.as_view(), name='appointment-update'),

    # Symptom URLs
    path('symptoms/', views.SymptomListView.as_view(), name='symptom-list'),
    path('symptoms/create/', views.SymptomCreateView.as_view(),
         name='symptom-create'),
    path('patients/<int:patient_id>/add-symptom/',
         views.patient_symptom_record_add, name='patient-add-symptom'),

    # API endpoints
    path('api/disease/<str:disease_type>/',
         views.get_disease_data, name='api-disease-data'),
    path('api/calendar-appointments/', views.calendar_appointments,
         name='api-calendar-appointments'),
]
