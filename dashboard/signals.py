# dashboard/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DiseaseCase
from accounts.models import User
from .models import Doctor
from .utils import update_disease_statistics


@receiver(post_save, sender=DiseaseCase)
def update_statistics_on_case_save(sender, instance, created, **kwargs):
    """Update disease statistics when a case is created or updated"""
    # Get month and year from the diagnosis date
    month = instance.diagnosis_date.month
    year = instance.diagnosis_date.year

    # Update statistics for this disease and month/year
    update_disease_statistics(disease=instance.disease, month=month, year=year)


@receiver(post_delete, sender=DiseaseCase)
def update_statistics_on_case_delete(sender, instance, **kwargs):
    """Update disease statistics when a case is deleted"""
    # Get month and year from the diagnosis date
    month = instance.diagnosis_date.month
    year = instance.diagnosis_date.year

    # Update statistics for this disease and month/year
    update_disease_statistics(disease=instance.disease, month=month, year=year)


@receiver(post_save, sender=User)
def create_doctor_profile(sender, instance, created, **kwargs):
    if created:
        # Avoid duplicate doctor profiles
        Doctor.objects.get_or_create(user=instance)
