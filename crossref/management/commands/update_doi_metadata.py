"""
Re-send registered DOIs with their current metadata.

Crossref treats a deposit of a DOI it already knows as an update to that record,
so this is how a correction reaches a DOI that is already live: page numbers
filled in after registration, a fixed title or author list, or a duplicate DOI
pointed at the article that survived.

Nothing here can create a DOI, and a rejected update never clears a DOI from its
article — those DOIs are registered and permanent.
"""

from django.core.management.base import BaseCommand, CommandError

from crossref.console import force_utf8
from crossref.deposits import approve_and_submit, collect_update_entries, create_batch
from crossref.models import DepositBatch
from crossref.services import (
    CrossrefError, article_title, get_environment, get_site_config,
)

# Same safety rail as register_dois: a run larger than this is usually a mistake.
DEFAULT_MAX = 100


class Command(BaseCommand):
    help = "Re-deposit already-registered DOIs so Crossref picks up corrected metadata."

    def add_arguments(self, parser):
        parser.add_argument('--issue', type=int, default=None,
                            help="Only articles belonging to this Issue id.")
        parser.add_argument('--article', type=int, action='append', default=None,
                            help="Only this article id (repeatable).")
        parser.add_argument('--limit', type=int, default=0,
                            help="Update at most N articles (0 = no limit).")
        parser.add_argument('--max', type=int, default=DEFAULT_MAX,
                            help=f"Refuse to send more than N articles at once (default {DEFAULT_MAX}).")
        parser.add_argument('--force', action='store_true',
                            help="Send even when the batch is larger than --max.")
        parser.add_argument('--redirect-to', type=int, default=None,
                            help="Point every DOI in this run at article N's page instead of "
                                 "its own. For a duplicate DOI that should resolve to the "
                                 "article that survived.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Print what would be sent and send nothing.")

    def handle(self, *args, **options):
        force_utf8(self.stdout, self.stderr)
        try:
            self._run(**options)
        except CrossrefError as exc:
            raise CommandError(str(exc))

    def _run(self, **options):
        site_config = get_site_config()
        environment = get_environment()

        override = None
        if options['redirect_to']:
            override = self._redirect_map(options)

        entries, skipped = collect_update_entries(
            issue_id=options['issue'], limit=options['limit'],
            article_ids=options['article'], resource_override=override,
        )

        for article, reason in skipped:
            label = article_title(article) or '(untitled)'
            self.stdout.write(self.style.WARNING(f"  skipped #{article.pk} {label[:60]} - {reason}"))

        if not entries:
            self.stdout.write("No registered DOIs matched. Nothing sent.")
            return

        self.stdout.write(f"{len(entries)} DOI(s) to update on {environment}:")
        for article, doi, url in entries:
            pages = f"{article.first_page}-{article.last_page}" if article.first_page else "no pages"
            self.stdout.write(f"  {doi}  ->  {url}   [{pages}]   {article_title(article)[:50]}")

        if options['dry_run']:
            self.stdout.write(self.style.NOTICE("[dry-run] nothing was sent."))
            return

        if len(entries) > options['max'] and not options['force']:
            raise CommandError(
                f"{len(entries)} articles is more than --max={options['max']}. Check the list "
                "above, then re-run with --limit for a smaller slice or --force."
            )

        batch = create_batch(
            entries, skipped, environment=environment, site_config=site_config,
            kind=DepositBatch.UPDATE,
            note=f"Queued by update_doi_metadata with {len(entries)} DOI(s) for {environment}.",
        )

        ok, message = approve_and_submit(batch, actor='update_doi_metadata')
        if not ok:
            raise CommandError(f"{batch.batch_id}: update failed - {message[:500]}")

        self.stdout.write(self.style.SUCCESS(
            f"{batch.batch_id}: {len(entries)} DOI(s) re-deposited to {environment}. "
            "Run check_doi_deposits later to confirm Crossref accepted the update."
        ))

    def _redirect_map(self, options):
        """Build {article pk: landing page of the target article} for --redirect-to."""
        from crossref.services import build_resource_url, get_site_base_url
        from issue.models import JournalIssue

        if not options['article']:
            raise CommandError("--redirect-to needs --article to say which DOI(s) to redirect.")
        try:
            target = JournalIssue.objects.get(pk=options['redirect_to'])
        except JournalIssue.DoesNotExist:
            raise CommandError(f"--redirect-to article #{options['redirect_to']} does not exist.")
        if options['redirect_to'] in options['article']:
            raise CommandError("--redirect-to article is also in --article; that is a no-op.")

        url = build_resource_url(target, get_site_base_url())
        self.stdout.write(self.style.NOTICE(f"Every DOI in this run will resolve to {url}"))
        return {pk: url for pk in options['article']}
