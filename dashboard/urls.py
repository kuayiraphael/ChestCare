# # dashboard/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import api_views
# from . import views

# # Create a router for REST API
# router = DefaultRouter()
# router.register('diseases', api_views.DiseaseViewSet)
# router.register('patients', api_views.PatientViewSet)
# router.register('doctors', api_views.DoctorViewSet)
# router.register('cases', api_views.DiseaseCaseViewSet)
# router.register('appointments', api_views.AppointmentViewSet)
# router.register('symptoms', api_views.SymptomViewSet)
# router.register('symptom-records', api_views.PatientSymptomRecordViewSet)

# urlpatterns = [
#     # API endpoints
#     path('api/', include(router.urls)),

#     # Dashboard summary
#     path('api/dashboard-summary/', api_views.api_dashboard_summary,
#          name='api-dashboard-summary'),

#     # Disease trends
#     path('api/disease-trends/', api_views.api_disease_trends,
#          name='api-disease-trends'),

#     # Current user info
#     path('api/current-user/', api_views.api_current_user_info,
#          name='api-current-user'),

#     path('api/generate-past-statistics/', api_views.generate_past_statistics,
#          name='api-generate-past-statistics'),

#     path('api/doctor-patients/', views.doctor_patients, name='doctor-patients'),
#     path('api/create-appointment/', views.create_appointment,
#          name='create-appointment'),
#     path('api/patients/',
#          api_views.PatientViewSet.as_view({'get': 'list'}), name='api-patients'),

#     path('api/calendar-appointments/',views.calendar_appointments,
#          name='calendar-appointments'),
#     path('api/doctor-appointments/', views.doctor_appointments,
#          name='doctor-appointments'),

# ]
# dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from . import views

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

    # Doctor-specific endpoints that were missing
    path('api/doctors/profile/', api_views.DoctorViewSet.as_view({'get': 'get_current_doctor_profile'}),
         name='api-doctor-profile'),
    path('api/doctors/dashboard-stats/', api_views.DoctorViewSet.as_view({'get': 'get_dashboard_stats'}),
         name='api-doctor-dashboard-stats'),

    # Appointment-specific endpoints that were missing
    path('api/appointments/upcoming/', api_views.AppointmentViewSet.as_view({'get': 'upcoming_appointments'}),
         name='api-appointments-upcoming'),
    path('api/appointments/today/', api_views.AppointmentViewSet.as_view({'get': 'today_appointments'}),
         name='api-appointments-today'),
    path('api/appointments/<int:pk>/cancel/', api_views.AppointmentViewSet.as_view({'patch': 'cancel_appointment'}),
         name='api-appointment-cancel'),
    path('api/appointments/<int:pk>/complete/', api_views.AppointmentViewSet.as_view({'patch': 'complete_appointment'}),
         name='api-appointment-complete'),
    path('api/appointments/<int:pk>/reschedule/', api_views.AppointmentViewSet.as_view({'patch': 'reschedule_appointment'}),
         name='api-appointment-reschedule'),

    # Existing endpoints
    path('api/doctor-patients/', views.doctor_patients, name='doctor-patients'),
    path('api/create-appointment/', views.create_appointment,
         name='create-appointment'),
    path('api/patients/',
         api_views.PatientViewSet.as_view({'get': 'list'}), name='api-patients'),

    path('api/calendar-appointments/', views.calendar_appointments,
         name='calendar-appointments'),
    path('api/doctor-appointments/', views.doctor_appointments,
         name='doctor-appointments'),
]
