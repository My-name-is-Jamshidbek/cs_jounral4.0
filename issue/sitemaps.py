from django.contrib.sitemaps import Sitemap
from .models import Issue, JournalIssue

class IssueSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Issue.objects.all().order_by('-publication_date')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        from django.urls import reverse
        return reverse('item_issue', kwargs={'pk': obj.pk})

class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return JournalIssue.objects.all().order_by('-publication_date')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()

