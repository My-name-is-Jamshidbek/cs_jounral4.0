from django.conf import settings
from django.db import models


class DepositBatch(models.Model):
    """
    One Crossref deposit run, queued by the `queue_doi_deposits` cron command.

    A batch is created in `pending` state and is never sent until a human
    approves it in the admin. That is deliberate: a registered DOI cannot be
    deleted, so nothing leaves this server without review.
    """

    PENDING = 'pending'
    SUBMITTED = 'submitted'
    REGISTERED = 'registered'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending review'),
        (SUBMITTED, 'Submitted to Crossref'),
        (REGISTERED, 'Registered'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]

    batch_id = models.CharField(
        max_length=100, unique=True,
        help_text="doi_batch_id sent to Crossref; also the key used to poll for results."
    )
    environment = models.CharField(
        max_length=20, choices=[('sandbox', 'Sandbox (test.crossref.org)'),
                                ('production', 'Production (doi.crossref.org)')],
        default='sandbox',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    xml = models.TextField(help_text="Exact deposit XML that will be sent to Crossref.")
    log = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='approved_doi_batches',
    )
    submitted_at = models.DateTimeField(blank=True, null=True)
    checked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'DOI deposit batch'
        verbose_name_plural = 'DOI deposit batches'
        ordering = ['-created_at']
        db_table = 'crossref_deposit_batch'

    def __str__(self):
        return f"{self.batch_id} ({self.get_status_display()}, {self.item_count} article(s))"

    @property
    def item_count(self):
        return self.items.count()

    @property
    def is_editable(self):
        """Only a pending batch may still be approved or cancelled."""
        return self.status == self.PENDING

    def append_log(self, message):
        from django.utils import timezone
        stamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log = f"{self.log}[{stamp}] {message}\n" if self.log else f"[{stamp}] {message}\n"


class DepositItem(models.Model):
    """One article inside a batch, with the DOI proposed for it."""

    PENDING = 'pending'
    DEPOSITED = 'deposited'
    REGISTERED = 'registered'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending review'),
        (DEPOSITED, 'Sent to Crossref'),
        (REGISTERED, 'Registered'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]

    batch = models.ForeignKey(DepositBatch, on_delete=models.CASCADE, related_name='items')
    article = models.ForeignKey(
        'issue.JournalIssue', on_delete=models.CASCADE, related_name='doi_deposits',
    )
    proposed_doi = models.CharField(max_length=100)
    resource_url = models.URLField(
        max_length=500,
        help_text="Landing page Crossref will resolve the DOI to. Must be publicly reachable.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    note = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'DOI deposit item'
        verbose_name_plural = 'DOI deposit items'
        ordering = ['id']
        db_table = 'crossref_deposit_item'
        constraints = [
            models.UniqueConstraint(fields=['batch', 'article'], name='unique_article_per_batch'),
        ]

    def __str__(self):
        return f"{self.proposed_doi} — {self.article_id}"
