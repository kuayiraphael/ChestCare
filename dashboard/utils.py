# dashboard/utils.py
from datetime import datetime
from django.db.models import Count
from .models import DiseaseCase, DiseaseStatistic, Disease
import cloudinary.uploader
from django.conf import settings

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


def upload_image_to_cloudinary(image_file, folder, public_id=None, transformation=None):
    """
    Upload an image to Cloudinary
    
    Args:
        image_file: The image file to upload
        folder: Cloudinary folder to store the image
        public_id: Optional public ID for the image
        transformation: Optional transformation parameters
    
    Returns:
        dict: Upload result containing URL and other metadata
    """
    try:
        upload_params = {
            'folder': folder,
            'resource_type': 'image',
            'overwrite': True,
        }

        if public_id:
            upload_params['public_id'] = public_id

        if transformation:
            upload_params['transformation'] = transformation
        else:
            # Default transformation for profile pictures
            upload_params['transformation'] = [
                {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
                {'quality': 'auto', 'fetch_format': 'auto'}
            ]

        result = cloudinary.uploader.upload(image_file, **upload_params)
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'result': result
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def delete_image_from_cloudinary(public_id):
    """
    Delete an image from Cloudinary
    
    Args:
        public_id: The public ID of the image to delete
    
    Returns:
        dict: Deletion result
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {
            'success': True,
            'result': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
