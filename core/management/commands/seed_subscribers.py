from django.core.management.base import BaseCommand
import random
from faker import Faker

from core.models import Joining


class Command(BaseCommand):
    help = 'Seed database with fake mailing list subscribers for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of subscribers to create (default: 50)',
        )

    def handle(self, *args, **options):
        count = options['count']
        fake = Faker()

        self.stdout.write(f'Creating {count} fake mailing list subscribers...')

        countries = [
            'United Kingdom', 'United States', 'Canada', 'Australia',
            'Germany', 'France', 'Spain', 'Italy', 'Netherlands',
            'Sweden', 'Norway', 'Japan', 'South Korea', 'China',
            'India', 'Brazil', 'Mexico', 'Argentina', 'South Africa'
        ]

        institutions = [
            'Oxford University', 'Cambridge University', 'Harvard University',
            'Yale University', 'Stanford University', 'MIT', 'University College London',
            'King\'s College London', 'University of Edinburgh', 'University of Glasgow',
            'Sorbonne University', 'University of Berlin', 'University of Munich',
            'University of Toronto', 'McGill University', 'University of Sydney',
            'University of Melbourne', 'Tokyo University', 'Kyoto University',
            'Peking University', 'Tsinghua University', 'University of São Paulo',
            'Universidad Nacional Autónoma de México', 'University of Cape Town'
        ]

        created_count = 0
        for _ in range(count):
            # Generate fake data
            first_name = fake.first_name()
            last_name = fake.last_name()
            domain = fake.random_element(['ac.uk', 'edu', 'university.edu', 'uni.edu'])
            email = f"{first_name.lower()}.{last_name.lower()}@{fake.word()}.{domain}"
            institution = fake.random_element(institutions)
            country = fake.random_element(countries)

            subscriber, created = Joining.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'institution': institution,
                    'country': country
                }
            )

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new subscribers!')
        )
