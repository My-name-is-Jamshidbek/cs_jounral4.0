from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

from .models import Issue, JournalIssue


def default_language_url(path_name, **kwargs):
    """
    Build a URL in the default language, whoever is asking.

    sitemap.xml sits outside i18n_patterns, but LocaleMiddleware still sets the
    active language from the request — so the sitemap listed /ru/ URLs to a
    Russian-speaking crawler and /uz/ URLs to everyone else. Every article page
    declares its canonical URL in the default language, and a sitemap that
    disagrees with the canonical tag is a signal search engines discard.
    """
    with translation.override(settings.LANGUAGE_CODE):
        return reverse(path_name, kwargs=kwargs)


class IssueSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Issue.objects.all().order_by('-publication_date')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return default_language_url('item_issue', pk=obj.pk)


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return JournalIssue.objects.all().order_by('-publication_date')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return default_language_url('article_detail', pk=obj.pk)
