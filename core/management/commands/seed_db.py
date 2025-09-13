import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Joining, Default
from about.models import About
from issue.models import Issue, JournalIssue
from submit.models import Permission
from subscribe.models import Subscribe


class Command(BaseCommand):
    help = 'Seed database with sample data for all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Starting database seeding...')

        # Seed all models
        self.seed_defaults()
        self.seed_joining_requests()
        self.seed_about_content()
        self.seed_issues()
        self.seed_journal_issues()
        self.seed_permissions()
        self.seed_subscribe_content()

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with sample data!')
        )

    def clear_data(self):
        """Clear all existing data"""
        Subscribe.objects.all().delete()
        Permission.objects.all().delete()
        JournalIssue.objects.all().delete()
        Issue.objects.all().delete()
        About.objects.all().delete()
        Joining.objects.all().delete()
        Default.objects.all().delete()
        self.stdout.write('✓ Cleared existing data')

    def seed_defaults(self):
        """Seed Default model with configuration data"""
        defaults_data = [
            {
                'name': 'site_title',
                'value': 'Comparative Critical Studies'
            },
            {
                'name': 'site_description',
                'value': 'A leading journal for comparative literature and critical studies research.'
            },
            {
                'name': 'contact_email',
                'value': 'journals@eup.ed.ac.uk'
            },
            {
                'name': 'publisher',
                'value': 'Edinburgh University Press'
            },
            {
                'name': 'issn_print',
                'value': '1744-1854'
            },
            {
                'name': 'issn_online',
                'value': '1750-0109'
            },
            {
                'name': 'current_volume',
                'value': '21'
            },
            {
                'name': 'publication_frequency',
                'value': '3 issues per year'
            },
            {
                'name': 'submission_email',
                'value': 'ccs@ed.ac.uk'
            },
            {
                'name': 'society_name',
                'value': 'British Comparative Literature Association (BCLA)'
            }
        ]

        for data in defaults_data:
            Default.objects.get_or_create(
                name=data['name'],
                defaults={'value': data['value']}
            )

        self.stdout.write('✓ Seeded Default settings')

    def seed_joining_requests(self):
        """Seed Joining model with sample mailing list requests"""
        joining_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@university.ac.uk',
                'institution': 'Oxford University',
                'country': 'United Kingdom'
            },
            {
                'first_name': 'David',
                'last_name': 'Chen',
                'email': 'd.chen@cambridge.edu',
                'institution': 'Cambridge University',
                'country': 'United Kingdom'
            },
            {
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
                'email': 'maria.rodriguez@uam.es',
                'institution': 'Universidad Autónoma de Madrid',
                'country': 'Spain'
            },
            {
                'first_name': 'James',
                'last_name': 'Smith',
                'email': 'j.smith@yale.edu',
                'institution': 'Yale University',
                'country': 'United States'
            },
            {
                'first_name': 'Emma',
                'last_name': 'Thompson',
                'email': 'e.thompson@mcgill.ca',
                'institution': 'McGill University',
                'country': 'Canada'
            },
            {
                'first_name': 'Pierre',
                'last_name': 'Dubois',
                'email': 'pierre.dubois@sorbonne.fr',
                'institution': 'Sorbonne University',
                'country': 'France'
            },
            {
                'first_name': 'Hiroshi',
                'last_name': 'Tanaka',
                'email': 'h.tanaka@tokyo.ac.jp',
                'institution': 'University of Tokyo',
                'country': 'Japan'
            },
            {
                'first_name': 'Sarah',
                'last_name': 'Williams',
                'email': 'sarah.williams@sydney.edu.au',
                'institution': 'University of Sydney',
                'country': 'Australia'
            }
        ]

        for data in joining_data:
            Joining.objects.get_or_create(
                email=data['email'],
                defaults=data
            )

        self.stdout.write('✓ Seeded Joining requests')

    def seed_about_content(self):
        """Seed About model with journal information"""
        about_data = [
            {
                'title': 'About the Journal',
                'content': '''<p>Comparative Critical Studies is a peer-reviewed academic journal that publishes research in comparative literature, critical theory, and cultural studies. Established in 2004, the journal provides a forum for innovative scholarship that crosses linguistic, cultural, and disciplinary boundaries.</p>
                
                <p>The journal welcomes contributions that engage with:</p>
                <ul>
                <li>Comparative literary analysis across different cultures and languages</li>
                <li>Critical theory and its applications</li>
                <li>Cultural studies and interdisciplinary approaches</li>
                <li>Translation studies and world literature</li>
                <li>Postcolonial and decolonial perspectives</li>
                </ul>
                
                <p>Published three times a year by Edinburgh University Press, Comparative Critical Studies maintains the highest standards of academic excellence and peer review.</p>'''
            },
            {
                'title': 'Editorial Policy',
                'content': '''<p>Comparative Critical Studies is committed to publishing original research that advances the field of comparative literature and critical studies. All submissions undergo rigorous double-blind peer review to ensure academic quality and scholarly rigor.</p>
                
                <p>The journal particularly encourages submissions that:</p>
                <ul>
                <li>Offer innovative theoretical perspectives</li>
                <li>Bridge different cultural and linguistic traditions</li>
                <li>Engage with contemporary critical debates</li>
                <li>Demonstrate methodological sophistication</li>
                </ul>'''
            },
            {
                'title': 'History and Mission',
                'content': '''<p>Founded in 2004, Comparative Critical Studies emerged from the recognition that literary and cultural studies increasingly require transnational and interdisciplinary approaches. The journal's mission is to foster dialogue between different critical traditions and to promote innovative comparative methodologies.</p>
                
                <p>Over its two decades of publication, the journal has established itself as a leading venue for comparative literature scholarship, publishing work by both established and emerging scholars from around the world.</p>'''
            }
        ]

        for data in about_data:
            About.objects.get_or_create(
                title=data['title'],
                defaults={'content': data['content']}
            )

        self.stdout.write('✓ Seeded About content')

    def seed_issues(self):
        """Seed Issue model with journal issues"""
        issues_data = [
            {
                'title': 'Special Issue: Postcolonial Modernisms',
                'volume': '21',
                'issue_number': '1',
                'description': 'This special issue explores the intersections between postcolonial studies and modernist aesthetics, examining how writers from formerly colonized territories engaged with and transformed modernist literary forms.',
                'publication_date': timezone.now() - timedelta(days=120),
            },
            {
                'title': 'Comparative Poetics: East and West',
                'volume': '21',
                'issue_number': '2',
                'description': 'An exploration of poetic traditions across Eastern and Western literary cultures, investigating shared themes, divergent forms, and cross-cultural influences.',
                'publication_date': timezone.now() - timedelta(days=60),
            },
            {
                'title': 'Digital Humanities and Comparative Literature',
                'volume': '21',
                'issue_number': '3',
                'description': 'This issue examines how digital tools and methodologies are transforming comparative literary studies, from distant reading to digital archives.',
                'publication_date': timezone.now() + timedelta(days=30),
            },
            {
                'title': 'Translation and World Literature',
                'volume': '20',
                'issue_number': '3',
                'description': 'Investigating the role of translation in creating and circulating world literature, with attention to power dynamics and cultural mediation.',
                'publication_date': timezone.now() - timedelta(days=200),
            },
            {
                'title': 'Ecocriticism and Comparative Studies',
                'volume': '20',
                'issue_number': '2',
                'description': 'A comparative examination of environmental themes in literature across different cultural contexts and ecological imaginaries.',
                'publication_date': timezone.now() - timedelta(days=280),
            }
        ]

        for data in issues_data:
            Issue.objects.get_or_create(
                volume=data['volume'],
                issue_number=data['issue_number'],
                defaults=data
            )

        self.stdout.write('✓ Seeded Issues')

    def seed_journal_issues(self):
        """Seed JournalIssue model with individual articles"""
        # Get existing issues to link articles
        issues = Issue.objects.all()

        articles_data = [
            {
                'title': 'Decolonizing Modernism: Virginia Woolf and Ama Ata Aidoo',
                'description': 'This article examines how Ghanaian writer Ama Ata Aidoo engages with and transforms Virginia Woolf\'s modernist techniques to address postcolonial concerns.',
                'authors': 'Dr. Kwame Asante',
                'accessability': 'open_access',
            },
            {
                'title': 'Stream of Consciousness in Arabic and English Literature',
                'description': 'A comparative analysis of stream of consciousness techniques in the works of James Joyce and Jabra Ibrahim Jabra.',
                'authors': 'Prof. Layla Al-Rashid',
                'accessability': 'restricted',
            },
            {
                'title': 'The Aesthetics of Fragmentation in Postcolonial Poetry',
                'description': 'Exploring how fragmentation operates as both modernist technique and postcolonial strategy in contemporary poetry.',
                'authors': 'Dr. Priya Sharma',
                'accessability': 'open_access',
            },
            {
                'title': 'Haiku and Imagism: A Transpacific Dialogue',
                'description': 'Examining the influence of Japanese haiku on Anglo-American Imagist poetry and the cultural translations involved.',
                'authors': 'Prof. Yuki Tanaka, Dr. Robert Chen',
                'accessability': 'subscription',
            },
            {
                'title': 'Ghazal Traditions: Persian, Urdu, and English Adaptations',
                'description': 'A comparative study of the ghazal form across Persian, Urdu, and English literary traditions.',
                'authors': 'Dr. Farid Hassan',
                'accessability': 'open_access',
            },
            {
                'title': 'Digital Archives and Literary Memory',
                'description': 'How digital humanities tools are reshaping our understanding of literary history and canon formation.',
                'authors': 'Prof. Elena Rodriguez, Dr. Michael Zhang',
                'accessability': 'subscription',
            },
            {
                'title': 'Machine Translation and Comparative Literature',
                'description': 'The implications of AI translation technologies for comparative literary studies and cross-cultural understanding.',
                'authors': 'Dr. Sarah Kim',
                'accessability': 'open_access',
            },
            {
                'title': 'Distant Reading and World Literature Canons',
                'description': 'Using computational methods to analyze patterns in world literature anthologies and curricula.',
                'authors': 'Prof. James Wilson',
                'accessability': 'restricted',
            }
        ]

        for i, data in enumerate(articles_data):
            if issues.exists():
                # Distribute articles across issues
                issue = issues[i % len(issues)]
                data.update({
                    'issue': issue,
                    'volume': issue.volume,
                    'issue_number': issue.issue_number,
                    'publication_date': issue.publication_date,
                    'views': random.randint(50, 500)
                })

                JournalIssue.objects.get_or_create(
                    title=data['title'],
                    defaults=data
                )

        self.stdout.write('✓ Seeded Journal articles')

    def seed_permissions(self):
        """Seed Permission model with access and usage information"""
        permissions_data = [
            {
                'name': 'Open Access Policy',
                'description': '''<p>Comparative Critical Studies supports open access to research. Authors may deposit their accepted manuscripts in institutional repositories after a 12-month embargo period.</p>
                
                <p>Key points:</p>
                <ul>
                <li>Authors retain copyright</li>
                <li>12-month embargo for repository deposit</li>
                <li>CC BY-NC-ND license for open access articles</li>
                </ul>'''
            },
            {
                'name': 'Copyright and Permissions',
                'description': '''<p>All articles published in Comparative Critical Studies are protected by copyright. Requests for permission to reproduce material should be directed to the publisher.</p>
                
                <p>For permission requests, please contact:</p>
                <ul>
                <li>Email: permissions@eup.ed.ac.uk</li>
                <li>Include full citation details</li>
                <li>Specify intended use</li>
                </ul>'''
            },
            {
                'name': 'Fair Use Guidelines',
                'description': '''<p>Limited quotation from articles is permitted under fair use provisions for:</p>
                <ul>
                <li>Academic research and teaching</li>
                <li>Critical commentary</li>
                <li>News reporting</li>
                </ul>
                
                <p>All quotations must include proper attribution and citation.</p>'''
            },
            {
                'name': 'Institutional Access',
                'description': '''<p>Institutions can access Comparative Critical Studies through:</p>
                <ul>
                <li>Direct subscription with Edinburgh University Press</li>
                <li>Consortium agreements</li>
                <li>Subject collections</li>
                </ul>
                
                <p>Contact our institutional sales team for pricing and access options.</p>'''
            },
            {
                'name': 'Individual Subscriptions',
                'description': '''<p>Individual researchers can subscribe to Comparative Critical Studies:</p>
                <ul>
                <li>Print + Online: £85/$135 per year</li>
                <li>Online only: £75/$120 per year</li>
                <li>Student rate: £45/$70 per year (with verification)</li>
                </ul>
                
                <p>BCLA members receive discounted subscription rates.</p>'''
            }
        ]

        for data in permissions_data:
            Permission.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )

        self.stdout.write('✓ Seeded Permissions')

    def seed_subscribe_content(self):
        """Seed Subscribe model with subscription page content"""
        subscribe_data = [
            {
                'title': 'Individual Subscribers and Society Members',
                'content': '''<p>Please select your subscription format from the options below:</p>
                
                <h4>Print + Online Subscription</h4>
                <ul>
                <li>Individual: £85 / $135 per year</li>
                <li>Student: £45 / $70 per year (with verification)</li>
                <li>BCLA Member: £65 / $105 per year</li>
                </ul>
                
                <h4>Online Only Subscription</h4>
                <ul>
                <li>Individual: £75 / $120 per year</li>
                <li>Student: £40 / $65 per year (with verification)</li>
                <li>BCLA Member: £55 / $90 per year</li>
                </ul>
                
                <p><a href="#" class="text-blue-600 underline">Subscribe now</a> or <a href="#" class="text-blue-600 underline">renew your subscription</a></p>''',
                'type': 'main'
            },
            {
                'title': 'Institutions and Libraries',
                'content': '''<p>To subscribe directly, please contact our Subscriptions team at <a href="mailto:journals@eup.ed.ac.uk" class="text-blue-600 underline">journals@eup.ed.ac.uk</a> or place an order via your usual subscription agent.</p>
                
                <h4>Institutional Pricing (2025)</h4>
                <ul>
                <li>Print + Online: £295 / $470</li>
                <li>Online Only: £265 / $425</li>
                <li>Print Only: £245 / $390</li>
                </ul>
                
                <p>Librarians, please visit <a href="#" class="text-blue-600 underline">Customer Services</a> for information on activation, site licence, usage statistics, archiving and preservation.</p>
                
                <p>For more information on journal collection options and pricing <a href="#" class="text-blue-600 underline">click here</a> or contact our Subscriptions Team at <a href="mailto:journals@eup.ed.ac.uk" class="text-blue-600 underline">journals@eup.ed.ac.uk</a> or on +44(0)131 650 4218.</p>''',
                'type': 'main'
            },
            {
                'title': 'Subscription Information',
                'content': '''<p>Print & Online and Online subscriptions include perpetual access to content from the years subscribed, plus access to back content since 2005, where available, during the subscription period.</p>
                
                <p>Prices for print subscriptions include delivery fees.</p>
                
                <p>All subscriptions and memberships are based on the calendar year (January-December).</p>
                
                <p>Online access starts from January in the subscription year.</p>
                
                <p>Pre-payment is required for all orders and renewals.</p>
                
                <p>Subscription and membership fees are non-refundable after the first issue of the year is published.</p>''',
                'type': 'sidebar'
            },
            {
                'title': 'Society Information',
                'content': '''<p>Members of the British Comparative Literature Association (BCLA) receive a journal subscription with their membership.</p>
                
                <p>Please visit <a href="https://www.bcla.org/" class="text-blue-600 underline">www.bcla.org</a> for further information and to join the society.</p>
                
                <p>BCLA members enjoy:</p>
                <ul>
                <li>Discounted journal subscription</li>
                <li>Access to annual conference</li>
                <li>Networking opportunities</li>
                <li>Career development resources</li>
                </ul>''',
                'type': 'sidebar'
            },
            {
                'title': 'Pay Per View - Articles',
                'content': '''<p>To access a single article for 48 hours online, click on the article you wish to read and follow the instructions.</p>
                
                <p>48-hour article access costs £35/$45.</p>
                
                <p><strong>Buy 3 or more articles and receive a 25% discount!</strong></p>
                
                <p>Perfect for researchers who need occasional access to specific articles without a full subscription.</p>''',
                'type': 'sidebar'
            },
            {
                'title': 'Back Issues and Single Copies',
                'content': '''<p>Single issues from current/previous years can be purchased by individuals by contacting our Subscriptions department at <a href="mailto:journals@eup.ed.ac.uk" class="text-blue-600 underline">journals@eup.ed.ac.uk</a></p>
                
                <p>Alternatively, navigate to an article in the issue you would like to purchase and select the 'Get Access' button.</p>
                
                <p>Back issue pricing:</p>
                <ul>
                <li>Current year: £35 / $55</li>
                <li>Previous years: £25 / $40</li>
                </ul>''',
                'type': 'sidebar'
            },
            {
                'title': 'Journal Collections Pricing',
                'content': '''<p><a href="#" class="text-blue-600 underline">Click here</a> for information on the complete EUP journals collection and smaller subject collections.</p>
                
                <p>Available collections:</p>
                <ul>
                <li>Literature and Cultural Studies Collection</li>
                <li>Philosophy and Religious Studies Collection</li>
                <li>Complete EUP Journals Collection</li>
                </ul>
                
                <p>For further information on discounts or multiple subscriptions, please email <a href="mailto:journals@eup.ed.ac.uk" class="text-blue-600 underline">journals@eup.ed.ac.uk</a>.</p>''',
                'type': 'sidebar'
            },
            {
                'title': 'Edinburgh Journals Archive',
                'content': '''<p>Institutions may buy the Edinburgh Journals Archive outright, or subscribe on an annual basis.</p>
                
                <p>To find out more, visit our <a href="#" class="text-blue-600 underline">Edinburgh Journals Archive information page</a>.</p>
                
                <p>The Archive contains all available back content across our journals, providing comprehensive historical access for research institutions.</p>''',
                'type': 'sidebar'
            }
        ]

        for data in subscribe_data:
            Subscribe.objects.get_or_create(
                title=data['title'],
                defaults={'content': data['content'], 'type': data['type']}
            )

        self.stdout.write('✓ Seeded Subscribe content')
