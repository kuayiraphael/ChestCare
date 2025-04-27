# dashboard/management/commands/generate_statistics.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from dashboard.models import Disease, DiseaseCase, DiseaseStatistic
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Generate disease statistics for a specified date range'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disease-type',
            type=str,
            help='Specific disease type to generate statistics for',
            required=False
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format',
            required=False,
            default='2024-01-01'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format',
            required=False,
            default='2025-04-27'
        )

    def handle(self, *args, **options):
        disease_type = options.get('disease_type')
        start_date_str = options.get('start_date')
        end_date_str = options.get('end_date')

        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(
            end_date_str, '%Y-%m-%d').date() if end_date_str else timezone.now().date()

        # Get disease if type provided
        disease = None
        if disease_type:
            try:
                disease = Disease.objects.get(type=disease_type)
                self.stdout.write(self.style.SUCCESS(
                    f"Generating statistics for disease: {disease.name}"))
            except Disease.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Disease with type '{disease_type}' not found"))
                return
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Generating statistics for all diseases"))

        # Process each month in the range
        current_date = start_date
        months_processed = 0
        stats_created = []

        while current_date <= end_date:
            month = current_date.month
            year = current_date.year

            self.stdout.write(f"Processing {month}/{year}...")

            # Process either specific disease or all diseases
            diseases_to_process = [
                disease] if disease else Disease.objects.all()

            for disease_obj in diseases_to_process:
                # Count cases for this disease in this month/year
                cases = DiseaseCase.objects.filter(
                    disease=disease_obj,
                    diagnosis_date__month=month,
                    diagnosis_date__year=year
                )
                current_count = cases.count()

                # Get previous month for percent change calculation
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
                stat, created = DiseaseStatistic.objects.update_or_create(
                    disease=disease_obj,
                    month=month,
                    year=year,
                    defaults={
                        'case_count': current_count,
                        'percent_change': round(percent_change, 2)
                    }
                )

                action = "Created" if created else "Updated"
                self.stdout.write(
                    f"  {action} stats for {disease_obj.name}: {current_count} cases, {percent_change:.1f}% change")
                stats_created.append(f"{disease_obj.name} - {month}/{year}")

            months_processed += 1

            # Move to next month
            current_date = (
                current_date + relativedelta(months=1)).replace(day=1)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully updated statistics for {months_processed} months, {len(stats_created)} entries"
        ))
