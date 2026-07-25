from django.contrib import admin
from django.http import HttpResponse

from crossref.services import build_deposit_xml

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
    readonly_fields = ('created_at', 'updated_at', 'views')
    ordering = ('-publication_date',)
    date_hierarchy = 'publication_date'
    list_editable = ('accessability',)
    actions = ['export_crossref_xml']

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
