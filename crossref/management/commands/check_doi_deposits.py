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
                style = self.style.ERROR
            else:
                style = self.style.NOTICE

            batch.save(update_fields=['status', 'checked_at', 'log'])
            self.stdout.write(style(f"{batch.batch_id}: {state} — {message[:200]}"))
