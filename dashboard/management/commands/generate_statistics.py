# dashboard/management/commands/generate_statistics.py
from django.core.management.base import BaseCommand
from dashboard.models import Disease, DiseaseCase
from dashboard.utils import update_disease_statistics
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Generate disease statistics for all diseases and time periods'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Number of months to generate statistics for (default: 12)'
        )

    def handle(self, *args, **options):
        months = options['months']

        # Get the current date
        now = datetime.now()

        # Generate statistics for each month in the range
        for i in range(months):
            # Calculate the month and year
            date = now - relativedelta(months=i)
            month = date.month
            year = date.year

            # Update statistics for all diseases for this month
            update_disease_statistics(month=month, year=year)

            self.stdout.write(
                self.style.SUCCESS(f'Generated statistics for {month}/{year}')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated statistics for {months} months')
        )
