"""
Cron entry point: queue a DOI deposit batch for review.

This command NEVER contacts Crossref. It finds articles that still have no DOI,
mints one for each, renders the deposit XML and parks it in the admin under
Crossref DOI → DOI deposit batches. A human approves it there.

Use `register_dois` instead when the deposit should go out unattended.
"""

from django.core.management.base import BaseCommand, CommandError

from crossref.console import force_utf8
from crossref.deposits import collect_deposit_entries, create_batch
from crossref.services import (
    CrossrefError, article_title, get_environment, get_site_config,
)


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
        # A misconfiguration is an operator problem, not a crash: cron should log
        # one readable line and exit non-zero, not a twenty-line traceback.
        try:
            self._queue(**options)
        except CrossrefError as exc:
            raise CommandError(str(exc))

    def _queue(self, **options):
        site_config = get_site_config()
        entries, skipped = collect_deposit_entries(
            issue_id=options['issue'], limit=options['limit'], site_config=site_config,
        )

        for article, reason in skipped:
            label = article_title(article) or '(untitled)'
            self.stdout.write(self.style.WARNING(f"  skipped #{article.pk} {label[:60]} - {reason}"))

        if not entries:
            self.stdout.write("No articles are waiting for a DOI. Nothing queued.")
            return

        environment = get_environment()
        if options['dry_run']:
            self.stdout.write(self.style.NOTICE(f"[dry-run] would queue {len(entries)} article(s) ({environment}):"))
            for article, doi, url in entries:
                self.stdout.write(f"  {doi}  ->  {url}   {article_title(article)[:60]}")
            return

        batch = create_batch(
            entries, skipped, environment=environment, site_config=site_config,
            note=(f"Queued by queue_doi_deposits with {len(entries)} article(s) for {environment}. "
                  "Awaiting approval in the admin."),
        )

        # Keep console output pure ASCII: cron on Windows writes through a cp1252
        # console that raises UnicodeEncodeError on arrows and dashes.
        self.stdout.write(self.style.SUCCESS(
            f"Queued batch {batch.batch_id} with {len(entries)} article(s) for {environment}. "
            "Open the admin (Crossref DOI -> DOI deposit batches) to review and approve."
        ))
