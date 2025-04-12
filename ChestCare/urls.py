# chestcare/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', RedirectView.as_view(url='dashboard/'), name='home'),
    
]
