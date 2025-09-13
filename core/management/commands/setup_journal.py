from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Complete database reset and seeding workflow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--articles',
            type=int,
            default=20,
            help='Number of extra articles to create (default: 20)',
        )
        parser.add_argument(
            '--subscribers',
            type=int,
            default=30,
            help='Number of fake subscribers to create (default: 30)',
        )

    def handle(self, *args, **options):
        articles_count = options['articles']
        subscribers_count = options['subscribers']

        self.stdout.write(self.style.WARNING('🔄 Starting complete database setup...'))

        # 1. Clear and seed main data
        self.stdout.write('📋 Step 1: Seeding core data...')
        call_command('seed_db', '--clear')

        # 2. Add extra articles
        self.stdout.write(f'📰 Step 2: Adding {articles_count} additional articles...')
        call_command('seed_articles', '--count', str(articles_count))

        # 3. Add fake subscribers
        self.stdout.write(f'👥 Step 3: Adding {subscribers_count} fake subscribers...')
        call_command('seed_subscribers', '--count', str(subscribers_count))

        self.stdout.write(
            self.style.SUCCESS('🎉 Complete database setup finished!')
        )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 DATABASE SUMMARY:'))
        self.stdout.write('='*50)

        from core.models import Joining, Default
        from about.models import About
        from issue.models import Issue, JournalIssue
        from submit.models import Permission
        from subscribe.models import Subscribe

        self.stdout.write(f'📧 Mailing List Subscribers: {Joining.objects.count()}')
        self.stdout.write(f'⚙️  Site Settings: {Default.objects.count()}')
        self.stdout.write(f'ℹ️  About Pages: {About.objects.count()}')
        self.stdout.write(f'📖 Journal Issues: {Issue.objects.count()}')
        self.stdout.write(f'📝 Journal Articles: {JournalIssue.objects.count()}')
        self.stdout.write(f'🔐 Permission Pages: {Permission.objects.count()}')
        self.stdout.write(f'💳 Subscription Content: {Subscribe.objects.count()}')

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ Your journal website is ready to use!'))
        self.stdout.write('🌐 Visit /admin/ to manage content')
        self.stdout.write('📱 Test the mailing list form on your homepage')
        self.stdout.write('='*50)
