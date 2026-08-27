"""
One-shot DOI registration: mint, deposit and confirm without a human in the loop.

This is the command to run straight after adding articles. `queue_doi_deposits`
remains for the review-first workflow; this one does the same work and sends it,
so an article can never end up displaying a DOI that was never registered.

A registered DOI is permanent, so the automation is deliberately narrow: it only
ever touches articles with no DOI at all, it refuses to deposit an unexpectedly
large batch without --force, and --dry-run prints exactly what would be sent.
"""

import time

from django.core.management.base import BaseCommand, CommandError

from crossref.console import force_utf8
from crossref.deposits import (
    approve_and_submit, collect_deposit_entries, create_batch, record_batch_result,
)
from crossref.services import (
    CrossrefError, article_title, check_batch, get_environment, get_site_config,
)

# A safety rail, not a technical limit: a normal issue is a few dozen articles,
# so a run this large means something unintended (a restored database, a cleared
# doi column) and deserves a second look before anything permanent is sent.
DEFAULT_MAX = 100


class Command(BaseCommand):
    help = ("Mint, deposit and confirm DOIs for every article that has none yet. "
            "Unlike queue_doi_deposits this sends the batch immediately.")

    def add_arguments(self, parser):
        parser.add_argument('--issue', type=int, default=None,
                            help="Only articles belonging to this Issue id.")
        parser.add_argument('--limit', type=int, default=0,
                            help="Register at most N articles (0 = no limit).")
        parser.add_argument('--max', type=int, default=DEFAULT_MAX,
                            help=f"Refuse to deposit more than N articles at once (default {DEFAULT_MAX}).")
        parser.add_argument('--force', action='store_true',
                            help="Deposit even when the batch is larger than --max.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Print what would be registered and send nothing.")
        parser.add_argument('--wait', type=int, default=0,
                            help="After depositing, poll Crossref for up to N minutes "
                                 "and report whether the DOIs registered.")
        parser.add_argument('--poll-interval', type=int, default=60,
                            help="Seconds between polls while waiting (default 60).")

    def handle(self, *args, **options):
        force_utf8(self.stdout, self.stderr)
        # A misconfiguration is an operator problem, not a crash: log one
        # readable line and exit non-zero, not a twenty-line traceback.
        try:
            self._run(**options)
        except CrossrefError as exc:
            raise CommandError(str(exc))

    def _run(self, **options):
        site_config = get_site_config()
        environment = get_environment()

        entries, skipped = collect_deposit_entries(
            issue_id=options['issue'], limit=options['limit'], site_config=site_config,
        )

        for article, reason in skipped:
            label = article_title(article) or '(untitled)'
            self.stdout.write(self.style.WARNING(f"  skipped #{article.pk} {label[:60]} - {reason}"))

        if not entries:
            self.stdout.write("No articles are waiting for a DOI. Nothing registered.")
            return

        self.stdout.write(f"{len(entries)} article(s) to register on {environment}:")
        for article, doi, url in entries:
            self.stdout.write(f"  {doi}  ->  {url}   {article_title(article)[:60]}")

        if options['dry_run']:
            self.stdout.write(self.style.NOTICE("[dry-run] nothing was sent."))
            return

        if len(entries) > options['max'] and not options['force']:
            raise CommandError(
                f"{len(entries)} articles is more than --max={options['max']}. A registered DOI "
                "cannot be deleted, so check the list above, then re-run with --limit to do a "
                "smaller slice or --force if the whole batch really is correct."
            )

        batch = create_batch(
            entries, skipped, environment=environment, site_config=site_config,
            note=f"Queued by register_dois with {len(entries)} article(s) for {environment}.",
        )

        ok, message = approve_and_submit(batch, actor='register_dois')
        if not ok:
            raise CommandError(f"{batch.batch_id}: deposit failed - {message[:500]}")

        self.stdout.write(self.style.SUCCESS(
            f"{batch.batch_id}: {len(entries)} DOI(s) deposited to {environment} and written "
            "to their articles."
        ))

        if not options['wait']:
            self.stdout.write(
                "Crossref processes deposits asynchronously. Run check_doi_deposits later "
                "to confirm registration (a failed batch releases its DOIs there)."
            )
            return

        self._wait_for_result(batch, options['wait'], options['poll_interval'])

    def _wait_for_result(self, batch, minutes, interval):
        """
        Poll until Crossref answers or the deadline passes.

        Crossref usually answers within a few minutes, but a queued submission
        can sit longer; a timeout here is not a failure, it just means the
        result has to be collected by check_doi_deposits later.
        """
        deadline = time.monotonic() + minutes * 60
        while True:
            time.sleep(min(interval, max(1, deadline - time.monotonic())))
            state, message = check_batch(batch)
            if state in ('registered', 'failed'):
                record_batch_result(batch, state, message)
                style = self.style.SUCCESS if state == 'registered' else self.style.ERROR
                self.stdout.write(style(f"{batch.batch_id}: {state} - {message[:300]}"))
                if state == 'failed':
                    raise CommandError(
                        "Crossref rejected the batch; the DOIs have been released and the "
                        "articles are back in the queue."
                    )
                return
            if time.monotonic() >= deadline:
                batch.append_log(f"Still {state} after waiting {minutes} minute(s).")
                batch.save(update_fields=['log'])
                self.stdout.write(self.style.NOTICE(
                    f"{batch.batch_id}: still {state} after {minutes} minute(s). "
                    "Run check_doi_deposits later to collect the result."
                ))
                return
            self.stdout.write(f"  {state}; waiting...")
