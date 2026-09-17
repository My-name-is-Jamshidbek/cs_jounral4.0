from datetime import date

from django.test import TestCase, override_settings

from issue.models import Issue, JournalIssue

ORIGIN = 'https://journal.example'


@override_settings(SITE_BASE_URL=ORIGIN)
class CanonicalUrlTests(TestCase):
    """
    Every page is served under /uz/, /en/ and /ru/, and the site also answers on
    www. Search Console reported duplicates for both, so these pin down that each
    page names exactly one canonical address: the default language, on the
    SITE_BASE_URL host, whichever language and host it was requested on.
    """

    @classmethod
    def setUpTestData(cls):
        cls.issue = Issue.objects.create(
            title='12-son', volume='3', issue_number='12',
            publication_date=date(2026, 9, 5),
        )
        cls.article = JournalIssue.objects.create(
            issue=cls.issue, title='Test article', volume='3', issue_number='12',
            authors='Axmedova Aziza Komilovna', publication_date=date(2026, 9, 5),
            file='journal_issues/test-article.pdf',
        )

    def page(self, path, **extra):
        response = self.client.get(path, **extra)
        self.assertEqual(response.status_code, 200, path)
        return response.content.decode()

    def canonical_links(self, html):
        return [
            line.split('href="', 1)[1].split('"', 1)[0]
            for line in html.split('<link')
            if 'rel="canonical"' in line
        ]

    def assertCanonical(self, path, expected, **extra):
        self.assertEqual(self.canonical_links(self.page(path, **extra)), [f'{ORIGIN}{expected}'], path)

    def test_article_in_any_language_points_at_default_language(self):
        for lang in ('uz', 'en', 'ru'):
            self.assertCanonical(f'/{lang}/issue/article/{self.article.pk}/',
                                 f'/uz/issue/article/{self.article.pk}/')

    def test_article_declares_every_language_as_alternate(self):
        html = self.page(f'/en/issue/article/{self.article.pk}/')
        for lang in ('uz', 'en', 'ru'):
            self.assertIn(
                f'hreflang="{lang}" href="{ORIGIN}/{lang}/issue/article/{self.article.pk}/"', html,
            )
        self.assertIn('hreflang="x-default"', html)

    def test_issue_page_points_at_default_language(self):
        for lang in ('uz', 'en', 'ru'):
            self.assertCanonical(f'/{lang}/issue/{self.issue.pk}/', f'/uz/issue/{self.issue.pk}/')

    def test_current_issue_points_at_the_issue_permanent_url(self):
        # /issue/current/ repeats the latest issue's page and moves on when the
        # next one is published, so it must not compete with the permanent URL.
        self.assertCanonical('/en/issue/current/', f'/uz/issue/{self.issue.pk}/')

    def test_archive_and_home_point_at_default_language(self):
        self.assertCanonical('/ru/issue/all/', '/uz/issue/all/')
        self.assertCanonical('/en/', '/uz/')

    def test_query_string_is_not_part_of_the_canonical_url(self):
        self.assertCanonical('/uz/issue/all/?utm_source=x', '/uz/issue/all/')

    def test_search_results_are_noindex_and_have_no_canonical(self):
        html = self.page('/uz/issue/search/?q=test')
        self.assertEqual(self.canonical_links(html), [])
        self.assertIn('<meta name="robots" content="noindex,follow" />', html)

    def test_canonical_ignores_the_host_the_request_came_in_on(self):
        self.assertCanonical(f'/uz/issue/article/{self.article.pk}/',
                             f'/uz/issue/article/{self.article.pk}/', HTTP_HOST='mirror.example')

    def test_pdf_url_is_on_the_site_host(self):
        html = self.page(f'/uz/issue/article/{self.article.pk}/', HTTP_HOST='mirror.example')
        self.assertIn(
            f'<meta name="citation_pdf_url" content="{ORIGIN}/media/journal_issues/test-article.pdf" />',
            html,
        )


@override_settings(SITE_BASE_URL=ORIGIN)
class CanonicalHostRedirectTests(TestCase):
    def test_www_host_redirects_permanently_keeping_path_and_query(self):
        response = self.client.get('/uz/issue/all/?page=2', HTTP_HOST='www.journal.example')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], f'{ORIGIN}/uz/issue/all/?page=2')

    def test_other_hosts_are_not_redirected(self):
        response = self.client.get('/uz/issue/all/', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
