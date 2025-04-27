# dashboard/utils.py
from datetime import datetime
from django.db.models import Count
from .models import DiseaseCase, DiseaseStatistic, Disease


def update_disease_statistics(disease=None, month=None, year=None):
    """
    Update disease statistics for a specific disease and month/year
    If no parameters provided, updates statistics for all diseases for the current month/year
    """
    # If no specific month/year provided, use current
    if month is None or year is None:
        now = datetime.now()
        month = month or now.month
        year = year or now.year

    # Get all diseases or just the specified one
    diseases = [disease] if disease else Disease.objects.all()

    for disease_obj in diseases:
        # Count cases for this disease in this month/year
        cases = DiseaseCase.objects.filter(
            disease=disease_obj,
            diagnosis_date__month=month,
            diagnosis_date__year=year
        )
        current_count = cases.count()

        # Get the previous month's statistics for percent change calculation
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year

        try:
            prev_stat = DiseaseStatistic.objects.get(
                disease=disease_obj,
                month=prev_month,
                year=prev_year
            )
            prev_count = prev_stat.case_count
            percent_change = ((current_count - prev_count) /
                              prev_count * 100) if prev_count else 0
        except DiseaseStatistic.DoesNotExist:
            percent_change = 0

        # Update or create statistics record
        DiseaseStatistic.objects.update_or_create(
            disease=disease_obj,
            month=month,
            year=year,
            defaults={
                'case_count': current_count,
                'percent_change': round(percent_change, 2)
            }
        )

    return True
