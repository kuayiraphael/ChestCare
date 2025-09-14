from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_chest_disease, name='predict_chest_disease'),
    path('predictions/', views.get_all_predictions, name='get_all_predictions'),
    path('predictions/patient/<int:patient_id>/',
         views.get_patient_predictions, name='get_patient_predictions'),
    path('predictions/<int:prediction_id>/confirm/',
         views.confirm_prediction, name='confirm_prediction'),
    # New Grad-CAM endpoints
    path('predictions/<int:prediction_id>/gradcam/',
         views.get_gradcam_image, name='get_gradcam_image'),
    path('predictions/<int:prediction_id>/regenerate-gradcam/',
         views.regenerate_gradcam, name='regenerate_gradcam'),
    path('diseases/', views.get_available_diseases,
         name='get_available_diseases'),

]
