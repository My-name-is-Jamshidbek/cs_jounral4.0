"""
Cron entry point: queue a DOI deposit batch for review.

This command NEVER contacts Crossref. It finds articles that still have no DOI,
mints one for each, renders the deposit XML and parks it in the admin under
Crossref DOI → DOI deposit batches. A human approves it there.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from crossref.console import force_utf8
from crossref.models import DepositBatch, DepositItem
from crossref.services import (
    CrossrefError, build_deposit_xml, build_doi, build_resource_url,
    get_doi_prefix, get_environment, get_site_base_url, get_site_config, make_batch_id,
)
from issue.models import JournalIssue


class Command(BaseCommand):
    help = "Queue a Crossref deposit batch for every article that has no DOI yet (review required before sending)."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0,
                            help="Queue at most N articles (0 = no limit).")
        parser.add_argument('--issue', type=int, default=None,
                            help="Only articles belonging to this Issue id.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Print what would be queued without creating a batch.")

    def handle(self, *args, **options):
        force_utf8(self.stdout, self.stderr)
        try:
            site_config = get_site_config()
            prefix = get_doi_prefix(site_config)
            base_url = get_site_base_url()
        except CrossrefError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        # Articles already sitting in a batch that is pending or in flight must
        # not be queued a second time.
        in_flight = DepositItem.objects.filter(
            batch__status__in=[DepositBatch.PENDING, DepositBatch.SUBMITTED],
            status__in=[DepositItem.PENDING, DepositItem.DEPOSITED],
        ).values_list('article_id', flat=True)

        # doi is null=True *and* blank=True, so cover the empty-string case too.
        articles = (
            JournalIssue.objects
            .filter(Q(doi__isnull=True) | Q(doi__exact=''))
            .exclude(pk__in=in_flight)
            .select_related('issue')
            .order_by('issue_id', 'pk')
        )

        if options['issue']:
            articles = articles.filter(issue_id=options['issue'])
        if options['limit']:
            articles = articles[:options['limit']]

        articles = list(articles)
        if not articles:
            self.stdout.write("No articles are waiting for a DOI. Nothing queued.")
            return

        taken = set(
            JournalIssue.objects.exclude(doi__isnull=True).exclude(doi__exact='')
            .values_list('doi', flat=True)
        )
        taken |= set(
            DepositItem.objects
            .exclude(batch__status__in=[DepositBatch.FAILED, DepositBatch.CANCELLED])
            .values_list('proposed_doi', flat=True)
        )

        entries, skipped = [], []
        for article in articles:
            if not article.publication_date:
                skipped.append((article, "no publication date"))
                continue
            doi = build_doi(article, prefix, taken)
            taken.add(doi)
            entries.append((article, doi, build_resource_url(article, base_url)))

        for article, reason in skipped:
            self.stdout.write(self.style.WARNING(f"  skipped #{article.pk} {article.title[:60]} — {reason}"))

        if not entries:
            self.stdout.write("Nothing queueable after filtering. Nothing queued.")
            return

        environment = get_environment()
        batch_id = make_batch_id()
        xml = build_deposit_xml(entries, batch_id=batch_id, site_config=site_config)

        if options['dry_run']:
            self.stdout.write(self.style.NOTICE(f"[dry-run] would queue batch {batch_id} ({environment}):"))
            for article, doi, url in entries:
                self.stdout.write(f"  {doi}  ->  {url}   {article.title[:60]}")
            return

        with transaction.atomic():
            batch = DepositBatch.objects.create(
                batch_id=batch_id, environment=environment, xml=xml,
                status=DepositBatch.PENDING,
            )
            batch.append_log(
                f"Queued by queue_doi_deposits with {len(entries)} article(s) for {environment}. "
                "Awaiting approval in the admin."
            )
            if skipped:
                batch.append_log(f"{len(skipped)} article(s) skipped: " +
                                 "; ".join(f"#{a.pk} ({r})" for a, r in skipped))
            batch.save(update_fields=['log'])
            DepositItem.objects.bulk_create([
                DepositItem(batch=batch, article=article, proposed_doi=doi, resource_url=url)
                for article, doi, url in entries
            ])

        # Keep console output pure ASCII: cron on Windows writes through a cp1252
        # console that raises UnicodeEncodeError on arrows and dashes.
        self.stdout.write(self.style.SUCCESS(
            f"Queued batch {batch_id} with {len(entries)} article(s) for {environment}. "
            "Open the admin (Crossref DOI -> DOI deposit batches) to review and approve."
        ))
