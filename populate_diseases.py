# populate_diseases.py
from dashboard.models import Disease
import os
import django
import sys

# Setup Django environment FIRST before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChestCare.settings')
django.setup()

# Import models AFTER Django setup

# Disease data
diseases = [
    {
        'name': 'Cardiomegaly',
        'type': 'cardiomegaly',
        'description': 'Enlargement of the heart',
        'causes': 'High blood pressure, coronary artery disease, heart valve problems, cardiomyopathy',
        'symptoms': 'Shortness of breath, fatigue, swelling in legs and abdomen',
        'treatment': 'Medications, surgery, lifestyle changes',
        'clinical_notes': 'Regular monitoring of heart size and function recommended'
    },
    {
        'name': 'Pneumonia',
        'type': 'pneumonia',
        'description': 'Infection that inflames air sacs in lungs',
        'causes': 'Bacteria, viruses, fungi',
        'symptoms': 'Chest pain when breathing, cough with phlegm, fatigue, fever, sweating, chills',
        'treatment': 'Antibiotics, rest, fluids, fever reducers',
        'clinical_notes': 'Vaccination recommended for high-risk groups'
    },
    {
        'name': 'Tuberculosis',
        'type': 'tuberculosis',
        'description': 'Bacterial infection affecting primarily the lungs',
        'causes': 'Mycobacterium tuberculosis bacteria',
        'symptoms': 'Persistent cough, weight loss, night sweats, fever',
        'treatment': 'Long course of antibiotics (6-9 months)',
        'clinical_notes': 'Contact tracing important to prevent spread'
    },
    {
        'name': 'Pulmonary Hypertension',
        'type': 'pulmonary',
        'description': 'High blood pressure in the pulmonary arteries',
        'causes': 'Heart failure, blood clots, lung diseases, autoimmune disorders',
        'symptoms': 'Shortness of breath, fatigue, chest pain, swelling in ankles/legs',
        'treatment': 'Blood vessel dilators, diuretics, oxygen therapy',
        'clinical_notes': 'Regular echocardiograms to monitor progression'
    }
]


def populate_diseases():
    for disease_data in diseases:
        disease, created = Disease.objects.get_or_create(
            type=disease_data['type'],
            defaults=disease_data
        )

        status = "Created" if created else "Already exists"
        print(f"{status}: {disease.name}")


if __name__ == "__main__":
    populate_diseases()
