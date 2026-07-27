"""
Cron entry point: poll Crossref for the result of already-submitted batches.

Crossref processes deposits asynchronously, so a successful submission only
means "received". This command moves batches from `submitted` to `registered`
or `failed` once Crossref publishes a result.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from crossref.console import force_utf8
from crossref.models import DepositBatch, DepositItem
from crossref.services import check_batch


class Command(BaseCommand):
    help = "Poll Crossref for the outcome of submitted DOI deposit batches."

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=str, default=None,
                            help="Only check this batch_id.")

    def handle(self, *args, **options):
        force_utf8(self.stdout, self.stderr)
        batches = DepositBatch.objects.filter(status=DepositBatch.SUBMITTED)
        if options['batch']:
            batches = batches.filter(batch_id=options['batch'])

        if not batches.exists():
            self.stdout.write("No submitted batches are waiting for a result.")
            return

        for batch in batches:
            state, message = check_batch(batch)
            batch.checked_at = timezone.now()
            batch.append_log(f"Result check: {state} — {message}")

            if state == 'registered':
                batch.status = DepositBatch.REGISTERED
                batch.items.update(status=DepositItem.REGISTERED)
                style = self.style.SUCCESS
            elif state == 'failed':
                batch.status = DepositBatch.FAILED
                batch.items.update(status=DepositItem.FAILED)
                released = self._release_dois(batch)
                if released:
                    batch.append_log(f"Cleared {released} unregistered DOI(s) from their articles.")
                style = self.style.ERROR
            else:
                style = self.style.NOTICE

            batch.save(update_fields=['status', 'checked_at', 'log'])
            self.stdout.write(style(f"{batch.batch_id}: {state} - {message[:200]}"))

    def _release_dois(self, batch):
        """
        Take back the DOIs of a rejected batch.

        The DOI is written to the article at approval time, but Crossref only
        registers it later. When registration fails, that DOI resolves nowhere
        and — worse — makes the article look done, so the next cron run skips
        it forever. Clear it so the article returns to the queue.
        """
        released = 0
        for item in batch.items.select_related('article'):
            # Only take back the DOI this batch proposed: an editor may have
            # set a different one by hand in the meantime.
            if item.article.doi == item.proposed_doi:
                item.article.doi = None
                item.article.save(update_fields=['doi'])
                released += 1
        return released
