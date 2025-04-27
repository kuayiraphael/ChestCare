# populate_statistics.py
from dashboard.models import Disease, DiseaseStatistic
import os
import django
import sys
from datetime import datetime
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChestCare.settings')
django.setup()

# Import models after Django setup

# Data for Jan-Apr 2025
data = [
    # Format: (disease_type, month, year, case_count, percent_change)
    ('cardiomegaly', 1, 2025, 42, 5.0),
    ('cardiomegaly', 2, 2025, 38, -9.5),
    ('cardiomegaly', 3, 2025, 45, 18.4),
    ('cardiomegaly', 4, 2025, 49, 8.9),

    ('pneumonia', 1, 2025, 58, 3.6),
    ('pneumonia', 2, 2025, 73, 25.9),
    ('pneumonia', 3, 2025, 65, -11.0),
    ('pneumonia', 4, 2025, 52, -20.0),

    ('tuberculosis', 1, 2025, 29, -2.0),
    ('tuberculosis', 2, 2025, 31, 6.9),
    ('tuberculosis', 3, 2025, 27, -12.9),
    ('tuberculosis', 4, 2025, 25, -7.4),

    ('pulmonary', 1, 2025, 34, 9.7),
    ('pulmonary', 2, 2025, 37, 8.8),
    ('pulmonary', 3, 2025, 41, 10.8),
    ('pulmonary', 4, 2025, 39, -4.9),
]


def populate_statistics():
    for disease_type, month, year, count, percent in data:
        try:
            disease = Disease.objects.get(type=disease_type)

            # Create or update statistic
            stat, created = DiseaseStatistic.objects.update_or_create(
                disease=disease,
                month=month,
                year=year,
                defaults={
                    'case_count': count,
                    'percent_change': percent
                }
            )

            action = "Created" if created else "Updated"
            print(
                f"{action} statistics for {disease.name}, {month}/{year}: {count} cases ({percent}% change)")

        except Disease.DoesNotExist:
            print(f"Disease with type '{disease_type}' not found")


if __name__ == "__main__":
    populate_statistics()
