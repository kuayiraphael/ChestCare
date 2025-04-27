# dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
    # API endpoints
    path('api/', include(router.urls)),

    # Dashboard summary
    path('api/dashboard-summary/', api_views.api_dashboard_summary,
         name='api-dashboard-summary'),

    # Disease trends
    path('api/disease-trends/', api_views.api_disease_trends,
         name='api-disease-trends'),

    # Current user info
    path('api/current-user/', api_views.api_current_user_info,
         name='api-current-user'),

    path('api/generate-past-statistics/', api_views.generate_past_statistics,
         name='api-generate-past-statistics'),
]
