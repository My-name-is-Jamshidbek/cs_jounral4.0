from ckeditor.fields import RichTextField
from django.db import models
from django.urls import reverse
from django.utils import timezone

class Issue(models.Model):
    """
    Model to represent a journal issue.
    """
    title = models.CharField(max_length=200)
    description = RichTextField(blank=True, null=True)
    volume = models.CharField(max_length=50)
    issue_number = models.CharField(max_length=50)
    publication_date = models.DateField()
    cover_image = models.ImageField(upload_to='issue_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - Volume {self.volume}, Issue {self.issue_number}"

    class Meta:
        verbose_name = "Journal Issue"
        verbose_name_plural = "Journal Issues"
        ordering = ['-publication_date']
        db_table = 'issue'

class JournalIssue(models.Model):
    """
    Model to represent a journal issue with additional metadata.
    """
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='journal_issues')
    title = models.CharField(max_length=200)
    description = RichTextField(blank=True, null=True)
    volume = models.CharField(max_length=50)
    issue_number = models.CharField(max_length=50)
    accessability = models.CharField(max_length=50, choices=[
        ('open_access', 'Open Access'),
        ('subscription', 'Subscription'),
        ('restricted', 'Restricted')
    ], default='open_access')
    authors = models.CharField(max_length=200)
    file = models.FileField(upload_to='journal_issues/', blank=True, null=True)
    publication_date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Google Scholar fields
    scholar_cluster_id = models.CharField(max_length=100, blank=True, null=True)
    google_scholar_query = models.CharField(max_length=300, blank=True, null=True, help_text="Custom search query override; defaults to title + authors")
    citation_count = models.PositiveIntegerField(default=0)
    last_scholar_sync = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.issue.title} - {self.title} (Volume {self.volume}, Issue {self.issue_number})"

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'pk': self.pk})

    def update_scholar_metadata(self, force=False):
        try:
            from scholarly import scholarly
        except Exception:
            return False, "scholarly not installed"
        if not force and self.last_scholar_sync and (timezone.now() - self.last_scholar_sync).days < 1:
            return False, "recently updated"
        query = self.google_scholar_query or f"{self.title} {self.authors}".strip()
        if not query:
            return False, "no query"
        try:
            search = scholarly.search_pubs(query)
            best = None
            for _ in range(3):
                try:
                    cand = next(search)
                except StopIteration:
                    break
                title = (cand.get('bib', {}) or {}).get('title', '')
                if title and self.title.lower().split(':')[0] in title.lower():
                    best = cand
                    break
                if best is None:
                    best = cand
            if not best:
                return False, "no result"
            cited_by = best.get('num_citations') or best.get('citedby') or 0
            cluster_id = best.get('pubid') or best.get('container_type', {}).get('source')
            changed = cited_by != self.citation_count or cluster_id != self.scholar_cluster_id
            self.citation_count = cited_by
            self.scholar_cluster_id = cluster_id
            self.last_scholar_sync = timezone.now()
            self.save(update_fields=['citation_count', 'scholar_cluster_id', 'last_scholar_sync'])
            return changed, f"updated citations={cited_by}"
        except Exception as e:
            return False, f"error: {e}"
