from datetime import date

from django.test import TestCase

from issue.models import Issue, JournalIssue


class CanonicalUrlTests(TestCase):
    """
    Every page is served under /uz/, /en/ and /ru/. Search Console reported those
    copies as duplicates because only article pages declared a canonical URL, so
    these pin down that each page names exactly one canonical address, in the
    default language, whichever language it was requested in.
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
        )

    def canonical_links(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        html = response.content.decode()
        return html, [
            line.split('href="', 1)[1].split('"', 1)[0]
            for line in html.split('<link')
            if 'rel="canonical"' in line
        ]

    def assertCanonical(self, path, expected):
        _html, links = self.canonical_links(path)
        self.assertEqual(links, [f'http://testserver{expected}'], path)

    def test_article_in_any_language_points_at_default_language(self):
        for lang in ('uz', 'en', 'ru'):
            self.assertCanonical(f'/{lang}/issue/article/{self.article.pk}/',
                                 f'/uz/issue/article/{self.article.pk}/')

    def test_article_declares_every_language_as_alternate(self):
        html, _links = self.canonical_links(f'/en/issue/article/{self.article.pk}/')
        for lang in ('uz', 'en', 'ru'):
            self.assertIn(
                f'hreflang="{lang}" href="http://testserver/{lang}/issue/article/{self.article.pk}/"',
                html,
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
        html, links = self.canonical_links('/uz/issue/search/?q=test')
        self.assertEqual(links, [])
        self.assertIn('<meta name="robots" content="noindex,follow" />', html)
