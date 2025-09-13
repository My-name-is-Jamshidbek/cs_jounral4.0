from django.contrib import admin
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
    list_display = ('title', 'issue', 'volume', 'issue_number', 'accessability', 'authors', 'publication_date', 'views')
    list_filter = ('accessability', 'publication_date', 'volume', 'created_at')
    search_fields = ('title', 'description', 'authors', 'volume', 'issue_number')
    readonly_fields = ('created_at', 'updated_at', 'views')
    ordering = ('-publication_date',)
    date_hierarchy = 'publication_date'
    list_editable = ('accessability',)
