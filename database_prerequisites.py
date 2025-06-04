# database_prerequisites.py
"""
Script to verify prerequisites for disease data generation
Checks if diseases, patients, and doctors exist in the database
"""
import os
import django
import sys

# Setup Django environment first
# Change this to your project name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChestCare.settings')
django.setup()
from dashboard.models import Disease, Patient, Doctor

# Import models AFTER Django setup


def verify_prerequisites():
    """Check if the necessary prerequisites exist in the database"""

    # Check diseases
    all_diseases = Disease.objects.all()
    disease_count = all_diseases.count()
    if disease_count == 0:
        print(
            "❌ ERROR: No diseases found in database. Please create disease entries first.")
        return False
    else:
        print(f"✅ Found {disease_count} diseases:")
        for disease in all_diseases:
            print(f"  - {disease.name} (type: {disease.type})")

    # Check specific disease types
    required_types = ['pneumonia', 'tuberculosis', 'cardiomegaly', 'pulmonary']
    existing_types = set(Disease.objects.values_list('type', flat=True))

    missing_types = set(required_types) - existing_types
    if missing_types:
        print(f"❌ WARNING: Missing disease types: {', '.join(missing_types)}")
        print("   The data generator expects these disease types for proper distribution.")
    else:
        print(
            f"✅ All required disease types found: {', '.join(required_types)}")

    # Check patients
    patient_count = Patient.objects.count()
    if patient_count == 0:
        print(
            "❌ ERROR: No patients found in database. Please create patient records first.")
        return False
    else:
        print(f"✅ Found {patient_count} patients")

    # Check doctors
    doctor_count = Doctor.objects.count()
    if doctor_count == 0:
        print("❌ ERROR: No doctors found in database. Please create doctor records first.")
        return False
    else:
        print(f"✅ Found {doctor_count} doctors")

    print("\n✅ All prerequisites are met! You can run the disease data generator.")
    return True


if __name__ == "__main__":
    print("Verifying database prerequisites for disease data generation...")
    if not verify_prerequisites():
        print("\n❌ Prerequisites check failed. Please address the issues above before running data generation.")
        sys.exit(1)
    else:
        print("\nRun the following to generate disease case data:")
        print("python disease_data_generator.py")
