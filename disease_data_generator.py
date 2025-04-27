# disease_data_generator.py
"""
Script to generate realistic disease case data from Jan 2024 to April 2025
Run this script to populate the database with synthetic case data before
using the generate_past_statistics endpoint
"""
from dashboard.models import Disease, Patient, Doctor, DiseaseCase
import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChestCare.settings')
django.setup()


def generate_disease_cases(start_date, end_date):
    """Generate realistic disease case data between the specified dates"""
    print(f"Generating disease cases from {start_date} to {end_date}")

    # Get all available diseases, patients, and doctors
    diseases = list(Disease.objects.all())
    patients = list(Patient.objects.all())
    doctors = list(Doctor.objects.all())

    if not diseases:
        print("No diseases found in database")
        return

    if not patients:
        print("No patients found in database")
        return

    if not doctors:
        print("No doctors found in database")
        return

    # Disease case distribution weights
    # This makes some diseases more common than others
    disease_weights = {
        'pneumonia': 60,      # Most common
        'tuberculosis': 20,
        'cardiomegaly': 15,
        'pulmonary': 5        # Least common
    }

    # Monthly case counts will follow seasonal patterns
    # Winter months have more respiratory cases
    month_multipliers = {
        1: 1.6,   # January - high
        2: 1.5,   # February - high
        3: 1.3,   # March - moderately high
        4: 1.0,   # April - normal
        5: 0.8,   # May - below normal
        6: 0.6,   # June - low
        7: 0.5,   # July - low
        8: 0.5,   # August - low
        9: 0.7,   # September - slightly below normal
        10: 1.0,  # October - normal
        11: 1.2,  # November - above normal
        12: 1.5,  # December - high
    }

    # Track created cases to avoid duplicates
    created_cases = 0
    existing_cases = set(
        DiseaseCase.objects.filter(
            diagnosis_date__gte=start_date,
            diagnosis_date__lte=end_date
        ).values_list('patient_id', 'disease_id', 'diagnosis_date', flat=False)
    )

    # Generate cases day by day
    current_date = start_date
    while current_date <= end_date:
        # Base number of daily cases
        base_daily_cases = 15

        # Apply monthly multiplier
        monthly_multiplier = month_multipliers.get(current_date.month, 1.0)

        # Random variation (80% to 120% of expected)
        daily_variation = random.uniform(0.8, 1.2)

        # Calculate cases for this day
        num_cases = int(base_daily_cases *
                        monthly_multiplier * daily_variation)

        # Generate the cases
        for _ in range(num_cases):
            # Select disease based on weights
            disease = random.choices(
                [d for d in diseases if d.type in disease_weights],
                weights=[disease_weights.get(
                    d.type, 1) for d in diseases if d.type in disease_weights]
            )[0]

            # Select random patient and doctor
            patient = random.choice(patients)
            doctor = random.choice(doctors)

            # Skip if this case already exists
            case_key = (patient.id, disease.id, current_date)
            if case_key in existing_cases:
                continue

            # Add to tracking
            existing_cases.add(case_key)

            # Determine severity (weighted toward moderate)
            severity = random.choices(
                ['mild', 'moderate', 'severe'],
                weights=[30, 55, 15]
            )[0]

            # Create the case
            DiseaseCase.objects.create(
                patient=patient,
                disease=disease,
                doctor=doctor,
                diagnosis_date=current_date,
                severity=severity,
                notes=f"Auto-generated case for data population",
                status=random.choices(
                    ['active', 'recovered', 'worsened', 'deceased'],
                    weights=[40, 50, 8, 2]
                )[0]
            )
            created_cases += 1

        # Move to next day
        current_date += timedelta(days=1)

        # Progress indicator
        if current_date.day == 1:
            print(
                f"Generated data through {current_date.strftime('%B %Y')}, {created_cases} cases so far")

    print(f"Finished generating {created_cases} disease cases")
    return created_cases


if __name__ == "__main__":
    # Generate cases from January 2024 to April 2025
    start_date = datetime(2024, 1, 1).date()
    end_date = datetime(2025, 4, 27).date()  # Today's date in your scenario

    case_count = generate_disease_cases(start_date, end_date)
    print(f"Total cases generated: {case_count}")
    print(f"Now run the generate_past_statistics endpoint to create statistics from this data")
