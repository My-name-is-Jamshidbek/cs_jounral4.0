from ckeditor.fields import RichTextField
from django.db import models

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


    def __str__(self):
        return f"{self.issue.title} - {self.title} (Volume {self.volume}, Issue {self.issue_number})"

    class Meta:
        verbose_name = "Journal Issue Metadata"
        verbose_name_plural = "Journal Issue Metadata"
        db_table = 'journal_issue'