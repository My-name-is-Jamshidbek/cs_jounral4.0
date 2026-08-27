"""
Cron entry point: poll Crossref for the result of already-submitted batches.

Crossref processes deposits asynchronously, so a successful submission only
means "received". This command moves batches from `submitted` to `registered`
or `failed` once Crossref publishes a result — and takes back the DOIs of a
rejected batch so those articles return to the queue.

This must run on a schedule. Without it a rejected deposit leaves its articles
displaying DOIs that resolve nowhere, and nothing ever notices.
"""

from django.core.management.base import BaseCommand

from crossref.console import force_utf8
from crossref.deposits import record_batch_result
from crossref.models import DepositBatch
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
            record_batch_result(batch, state, message)
            style = {
                'registered': self.style.SUCCESS,
                'failed': self.style.ERROR,
            }.get(state, self.style.NOTICE)
            self.stdout.write(style(f"{batch.batch_id}: {state} - {message[:200]}"))
