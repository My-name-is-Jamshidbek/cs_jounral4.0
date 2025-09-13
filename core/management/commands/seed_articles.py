from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from issue.models import Issue, JournalIssue


class Command(BaseCommand):
    help = 'Seed database with additional journal issues and articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of articles to create (default: 10)',
        )

    def handle(self, *args, **options):
        count = options['count']

        self.stdout.write(f'Creating {count} additional journal articles...')

        # Sample article data
        article_templates = [
            {
                'title': 'Narrative Techniques in Contemporary World Literature',
                'authors': 'Dr. Elena Petrov',
                'description': 'An examination of innovative narrative strategies in recent global fiction.',
            },
            {
                'title': 'Translation Theory and Practice in the Digital Age',
                'authors': 'Prof. Ahmed Hassan, Dr. Lisa Chen',
                'description': 'How digital technologies are transforming translation practices and theory.',
            },
            {
                'title': 'Postcolonial Memory and Trauma Narratives',
                'authors': 'Dr. Amara Okafor',
                'description': 'Exploring how postcolonial literature represents collective memory and trauma.',
            },
            {
                'title': 'Gender and Power in Medieval Romance Traditions',
                'authors': 'Prof. Margaret Davies',
                'description': 'A comparative analysis of gender dynamics across medieval romance literature.',
            },
            {
                'title': 'Environmental Humanities and Climate Fiction',
                'authors': 'Dr. Carlos Rodriguez',
                'description': 'The emergence of climate fiction as a response to environmental crisis.',
            },
            {
                'title': 'Digital Poetry and Interactive Literature',
                'authors': 'Dr. Yuki Nakamura',
                'description': 'Exploring new forms of digital and interactive literary expression.',
            },
            {
                'title': 'Migration Narratives in Contemporary Literature',
                'authors': 'Prof. Fatima Al-Zahra',
                'description': 'How contemporary writers represent migration and displacement experiences.',
            },
            {
                'title': 'Artificial Intelligence and Literary Creativity',
                'authors': 'Dr. Robert Kim, Prof. Sarah Johnson',
                'description': 'The implications of AI for literary creation and criticism.',
            }
        ]

        # Get existing issues or create default ones
        issues = list(Issue.objects.all())
        if not issues:
            # Create a few default issues if none exist
            default_issue = Issue.objects.create(
                title='General Issue',
                volume='21',
                issue_number='1',
                description='General issue containing various articles',
                publication_date=timezone.now()
            )
            issues = [default_issue]

        created_count = 0
        for i in range(count):
            template = article_templates[i % len(article_templates)]
            issue = issues[i % len(issues)]

            article_data = {
                'title': f"{template['title']} ({i+1})",
                'authors': template['authors'],
                'description': template['description'],
                'issue': issue,
                'volume': issue.volume,
                'issue_number': issue.issue_number,
                'publication_date': issue.publication_date,
                'accessability': random.choice(['open_access', 'subscription', 'restricted']),
                'views': random.randint(10, 1000)
            }

            article, created = JournalIssue.objects.get_or_create(
                title=article_data['title'],
                defaults=article_data
            )

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new articles!')
        )
