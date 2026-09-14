"""
Canonical and alternate-language URLs for any page.

Every page is served under /uz/, /en/ and /ru/ (i18n_patterns), so each one
exists at three addresses with the same content. Without a canonical link Google
treats them as unrelated duplicates and picks one itself, which Search Console
reports as "duplicate without user-selected canonical". The default language is
the canonical address; the others are declared as hreflang alternates.
"""

from django.conf import settings
from django.urls import translate_url


def language_urls(request, path=None):
    """
    Return {language code: absolute URL} for a page in every site language.

    `path` defaults to the page being served. The query string is never carried
    over: a search query or a tracking parameter must not become part of the
    canonical address.
    """
    path = path or request.path
    return {
        code: request.build_absolute_uri(translate_url(path, code))
        for code, _name in settings.LANGUAGES
    }
