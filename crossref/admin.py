from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html

from .deposits import approve_and_submit
from .models import DepositBatch, DepositItem


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
            ok, message = approve_and_submit(batch, user=request.user, actor=str(request.user))
            if not ok:
                self.message_user(request, f"{batch.batch_id}: {message[:300]}", level=messages.ERROR)
                continue

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


@admin.register(DepositItem)
class DepositItemAdmin(admin.ModelAdmin):
    list_display = ('proposed_doi', 'article', 'batch', 'status')
    list_filter = ('status', 'batch__environment')
    search_fields = ('proposed_doi', 'article__title', 'batch__batch_id')
    readonly_fields = ('batch', 'article', 'proposed_doi', 'resource_url', 'status', 'note')

    def has_add_permission(self, request):
        return False
