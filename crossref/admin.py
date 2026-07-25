from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from issue.models import JournalIssue

from .models import DepositBatch, DepositItem
from .services import submit_batch


class DepositItemInline(admin.TabularInline):
    model = DepositItem
    extra = 0
    can_delete = False
    fields = ('article_link', 'proposed_doi', 'resource_url', 'status', 'note')
    readonly_fields = ('article_link', 'proposed_doi', 'resource_url', 'status', 'note')

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Article')
    def article_link(self, obj):
        return format_html(
            '<a href="/admin/issue/journalissue/{}/change/" target="_blank">{}</a>',
            obj.article_id, obj.article.title[:70],
        )


@admin.register(DepositBatch)
class DepositBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_id', 'status', 'environment', 'item_count', 'created_at', 'submitted_at', 'approved_by')
    list_filter = ('status', 'environment', 'created_at')
    search_fields = ('batch_id', 'log', 'items__proposed_doi')
    readonly_fields = (
        'batch_id', 'environment', 'status', 'created_at', 'approved_at', 'approved_by',
        'submitted_at', 'checked_at', 'log', 'xml_preview',
    )
    exclude = ('xml',)
    inlines = [DepositItemInline]
    ordering = ('-created_at',)
    actions = ['approve_and_deposit', 'cancel_batches', 'download_xml']

    def has_add_permission(self, request):
        # Batches are created by the queue_doi_deposits cron command only.
        return False

    @admin.display(description='Deposit XML (exactly what will be sent)')
    def xml_preview(self, obj):
        return format_html(
            '<textarea readonly rows="24" style="width:100%;font-family:monospace;font-size:12px">{}</textarea>',
            obj.xml,
        )

    @admin.action(description="Approve and deposit selected batches to Crossref")
    def approve_and_deposit(self, request, queryset):
        for batch in queryset:
            if not batch.is_editable:
                self.message_user(
                    request,
                    f"{batch.batch_id}: skipped — status is '{batch.get_status_display()}', only pending batches can be approved.",
                    level=messages.WARNING,
                )
                continue

            problem = self._validate(batch)
            if problem:
                batch.append_log(f"Approval refused: {problem}")
                batch.save(update_fields=['log'])
                self.message_user(request, f"{batch.batch_id}: {problem}", level=messages.ERROR)
                continue

            ok, message = submit_batch(batch)
            batch.approved_at = timezone.now()
            batch.approved_by = request.user
            batch.append_log(f"Approved by {request.user}. {message}")

            if not ok:
                batch.status = DepositBatch.FAILED
                batch.items.update(status=DepositItem.FAILED)
                batch.save(update_fields=['status', 'approved_at', 'approved_by', 'log'])
                self.message_user(request, f"{batch.batch_id}: deposit failed — {message[:300]}", level=messages.ERROR)
                continue

            with transaction.atomic():
                for item in batch.items.select_related('article'):
                    item.article.doi = item.proposed_doi
                    item.article.save(update_fields=['doi'])
                    item.status = DepositItem.DEPOSITED
                    item.save(update_fields=['status'])
                batch.status = DepositBatch.SUBMITTED
                batch.submitted_at = timezone.now()
                batch.save(update_fields=['status', 'submitted_at', 'approved_at', 'approved_by', 'log'])

            self.message_user(
                request,
                f"{batch.batch_id}: submitted to Crossref ({batch.environment}); "
                f"{batch.item_count} DOI(s) written to their articles. "
                "Crossref processes deposits asynchronously — run check_doi_deposits later to confirm registration.",
                level=messages.SUCCESS,
            )

    @admin.action(description="Cancel selected batches (do not deposit)")
    def cancel_batches(self, request, queryset):
        cancelled = 0
        for batch in queryset:
            if not batch.is_editable:
                self.message_user(
                    request,
                    f"{batch.batch_id}: cannot cancel — already {batch.get_status_display()}.",
                    level=messages.WARNING,
                )
                continue
            batch.status = DepositBatch.CANCELLED
            batch.append_log(f"Cancelled by {request.user}.")
            batch.save(update_fields=['status', 'log'])
            batch.items.update(status=DepositItem.CANCELLED)
            cancelled += 1
        if cancelled:
            self.message_user(request, f"{cancelled} batch(es) cancelled. Their articles will be re-queued on the next cron run.")

    @admin.action(description="Download deposit XML")
    def download_xml(self, request, queryset):
        batch = queryset.first()
        if queryset.count() != 1:
            self.message_user(request, "Select exactly one batch to download.", level=messages.WARNING)
            return
        response = HttpResponse(batch.xml, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{batch.batch_id}.xml"'
        return response

    def _validate(self, batch):
        """
        Re-check the batch against the live database. The XML was rendered when
        the batch was queued, so anything that changed since then makes it stale.
        """
        items = list(batch.items.select_related('article'))
        if not items:
            return "batch has no articles."

        already = [i for i in items if i.article.doi]
        if already:
            return (
                f"{len(already)} article(s) already have a DOI (e.g. #{already[0].article_id} = "
                f"{already[0].article.doi}). Cancel this batch and re-run queue_doi_deposits."
            )

        proposed = [i.proposed_doi for i in items]
        if len(set(proposed)) != len(proposed):
            return "the batch proposes the same DOI for more than one article."

        clash = (
            JournalIssue.objects.filter(doi__in=proposed)
            .exclude(pk__in=[i.article_id for i in items])
            .values_list('doi', flat=True)
        )
        if clash:
            return f"proposed DOI(s) already used by other articles: {', '.join(clash)}."
        return None


@admin.register(DepositItem)
class DepositItemAdmin(admin.ModelAdmin):
    list_display = ('proposed_doi', 'article', 'batch', 'status')
    list_filter = ('status', 'batch__environment')
    search_fields = ('proposed_doi', 'article__title', 'batch__batch_id')
    readonly_fields = ('batch', 'article', 'proposed_doi', 'resource_url', 'status', 'note')

    def has_add_permission(self, request):
        return False
