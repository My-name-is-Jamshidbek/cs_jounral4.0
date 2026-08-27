from django.contrib import admin, messages
from django.http import HttpResponse

from crossref.deposits import approve_and_submit, collect_deposit_entries, create_batch
from crossref.services import CrossrefError, article_title, build_deposit_xml, get_environment

from .models import Issue, JournalIssue


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'volume', 'issue_number', 'publication_date', 'created_at')
    list_filter = ('publication_date', 'volume', 'created_at')
    search_fields = ('title', 'description', 'volume', 'issue_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-publication_date',)
    date_hierarchy = 'publication_date'


@admin.register(JournalIssue)
class JournalIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'issue', 'volume', 'issue_number', 'accessability', 'doi', 'authors', 'publication_date', 'views')
    list_filter = ('accessability', 'publication_date', 'volume', 'created_at')
    search_fields = ('title', 'description', 'authors', 'volume', 'issue_number', 'doi')
    # doi is deliberately not editable here. A hand-typed DOI is displayed on the
    # article page but never deposited, and it permanently removes the article
    # from the deposit queue (which only picks up articles with no DOI) — which
    # is exactly how the September 2026 issue ended up advertising 31 DOIs that
    # Crossref had never heard of. DOIs are minted and written by the deposit
    # workflow only; use `register_dois` or the action below.
    readonly_fields = ('doi', 'created_at', 'updated_at', 'views')
    ordering = ('-publication_date',)
    date_hierarchy = 'publication_date'
    list_editable = ('accessability',)
    actions = ['register_dois_now', 'export_crossref_xml']

    @admin.action(description="Register DOIs with Crossref for selected articles")
    def register_dois_now(self, request, queryset):
        """
        Mint and deposit DOIs for the selected articles in one step.

        Articles that already have a DOI are left alone, so re-running this over
        a whole issue only ever picks up what is still missing.
        """
        try:
            entries, skipped = collect_deposit_entries(
                article_ids=list(queryset.values_list('pk', flat=True)),
            )
        except CrossrefError as exc:
            self.message_user(request, f"Crossref is not configured: {exc}", level=messages.ERROR)
            return

        for article, reason in skipped:
            self.message_user(
                request,
                f"#{article.pk} {article_title(article)[:60]} skipped — {reason}",
                level=messages.WARNING,
            )

        if not entries:
            self.message_user(
                request,
                "Nothing to register: the selected articles either already have a DOI, "
                "are already in a batch awaiting a result, or were skipped above.",
                level=messages.WARNING,
            )
            return

        environment = get_environment()
        batch = create_batch(
            entries, skipped, environment=environment,
            note=f"Queued from the article admin by {request.user} with {len(entries)} article(s).",
        )
        ok, message = approve_and_submit(batch, user=request.user, actor=str(request.user))
        if not ok:
            self.message_user(request, f"{batch.batch_id}: deposit failed — {message[:300]}", level=messages.ERROR)
            return

        self.message_user(
            request,
            f"{batch.batch_id}: {len(entries)} DOI(s) deposited to Crossref ({environment}) and "
            "written to their articles. Registration is asynchronous — check_doi_deposits "
            "confirms it, and releases the DOIs again if Crossref rejects the batch.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Export selected articles as Crossref deposit XML")
    def export_crossref_xml(self, request, queryset):
        """Manual escape hatch: download the XML for articles that already have a DOI."""
        with_doi = queryset.exclude(doi__isnull=True).exclude(doi__exact='').select_related('issue')
        skipped = queryset.count() - with_doi.count()
        if not with_doi.exists():
            self.message_user(request, "None of the selected articles have a DOI set. Add a DOI first.", level='error')
            return

        entries = [
            (article, article.doi, request.build_absolute_uri(article.get_absolute_url()))
            for article in with_doi.order_by('issue_id', 'id')
        ]
        xml = build_deposit_xml(entries)

        if skipped:
            self.message_user(request, f"{skipped} selected article(s) skipped (no DOI set).", level='warning')

        response = HttpResponse(xml, content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="crossref_deposit.xml"'
        return response
