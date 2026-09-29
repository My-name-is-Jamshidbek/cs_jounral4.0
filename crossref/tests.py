from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings

from crossref.deposits import (
    approve_and_submit, collect_redirect_entries, create_batch, record_batch_result,
    validate_batch,
)
from crossref.models import DepositBatch, DepositItem
from crossref.services import CrossrefError
from issue.models import Issue, JournalIssue

SITE = {
    'SITE_BASE_URL': 'https://journal.example',
    'CROSSREF_USERNAME': 'u', 'CROSSREF_PASSWORD': 'p',
    'CROSSREF_DEPOSIT_EMAIL': 'editor@journal.example',
}


@override_settings(**SITE)
class RedirectBatchTests(TestCase):
    """
    A duplicate article was deleted before its DOI was dealt with, so the DOI
    (permanent) resolves to a 404 and no row is left to re-deposit from. A
    redirect batch sends the surviving article's metadata under the surplus DOI.
    What must never happen: the surviving article losing its own DOI.
    """

    @classmethod
    def setUpTestData(cls):
        cls.issue = Issue.objects.create(
            title='1-son', volume='1', issue_number='1', publication_date=date(2024, 4, 24),
        )
        cls.survivor = JournalIssue.objects.create(
            issue=cls.issue, title='Tarjima', volume='1', issue_number='1',
            authors='Xalliyeva Gulnoz Iskandarovna', publication_date=date(2024, 4, 24),
            doi='10.64964/comp.2024.0054', first_page='45', last_page='55',
        )

    SURPLUS = '10.64964/comp.2024.0283'

    def redirect_batch(self):
        with patch('crossref.deposits.get_site_config', return_value={
            'doi_prefix': '10.64964', 'issn_print': 'Print ISSN: 3060-4559',
            'site_title': 'Journal', 'contact_email': 'editor@journal.example',
        }), patch('crossref.services.get_site_config', return_value={
            'doi_prefix': '10.64964', 'issn_print': 'Print ISSN: 3060-4559',
            'site_title': 'Journal', 'contact_email': 'editor@journal.example',
        }):
            entries = collect_redirect_entries({self.SURPLUS: self.survivor.pk})
            return create_batch(entries, kind=DepositBatch.REDIRECT)

    def test_entries_point_the_surplus_doi_at_the_survivor(self):
        with patch('crossref.deposits.get_site_config', return_value={'doi_prefix': '10.64964'}):
            entries = collect_redirect_entries({self.SURPLUS: self.survivor.pk})
        (article, doi, url), = entries
        self.assertEqual(article, self.survivor)
        self.assertEqual(doi, self.SURPLUS)
        self.assertEqual(url, f'https://journal.example/uz/issue/article/{self.survivor.pk}/')

    def test_refuses_a_doi_that_a_live_article_still_carries(self):
        with self.assertRaises(CrossrefError):
            collect_redirect_entries({self.survivor.doi: self.survivor.pk})

    def test_refuses_a_target_without_its_own_doi(self):
        bare = JournalIssue.objects.create(
            issue=self.issue, title='No DOI yet', volume='1', issue_number='1',
            authors='A B', publication_date=date(2024, 4, 24),
        )
        with self.assertRaises(CrossrefError):
            collect_redirect_entries({self.SURPLUS: bare.pk})

    def test_batch_validates_and_keeps_the_survivors_doi_after_submit(self):
        batch = self.redirect_batch()
        self.assertIsNone(validate_batch(batch))
        with patch('crossref.deposits.submit_batch', return_value=(True, 'ok')):
            ok, _message = approve_and_submit(batch, actor='test')
        self.assertTrue(ok)
        self.survivor.refresh_from_db()
        self.assertEqual(self.survivor.doi, '10.64964/comp.2024.0054')
        self.assertEqual(batch.items.get().status, DepositItem.DEPOSITED)

    def test_validation_fails_if_the_surplus_doi_reappears_on_an_article(self):
        batch = self.redirect_batch()
        JournalIssue.objects.create(
            issue=self.issue, title='Back again', volume='1', issue_number='1',
            authors='A B', publication_date=date(2024, 4, 24), doi=self.SURPLUS,
        )
        self.assertIn('live article', validate_batch(batch) or '')

    def test_failed_redirect_leaves_the_survivors_doi_alone(self):
        batch = self.redirect_batch()
        with patch('crossref.deposits.submit_batch', return_value=(True, 'ok')):
            approve_and_submit(batch, actor='test')
        record_batch_result(batch, 'failed', 'rejected')
        self.survivor.refresh_from_db()
        self.assertEqual(self.survivor.doi, '10.64964/comp.2024.0054')
        self.assertEqual(batch.status, DepositBatch.FAILED)
