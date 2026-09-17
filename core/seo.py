"""
Canonical and alternate-language URLs for any page.

Every page is served under /uz/, /en/ and /ru/ (i18n_patterns), so each one
exists at three addresses with the same content. Without a canonical link Google
treats them as unrelated duplicates and picks one itself, which Search Console
reports as "duplicate without user-selected canonical". The default language is
the canonical address; the others are declared as hreflang alternates.

Absolute URLs are built from SITE_BASE_URL, never from the host a request came in
on. The site also answers on www., and a canonical taken from the request made
the www copy declare itself canonical too: Google saw two whole sites each
claiming to be the original, and reported that its choice of canonical did not
match ours.
"""

from django.conf import settings
from django.urls import translate_url


def site_origin(request):
    """The scheme and host every absolute URL on the site is built from."""
    base = (getattr(settings, 'SITE_BASE_URL', '') or '').strip().rstrip('/')
    return base or f'{request.scheme}://{request.get_host()}'


def language_urls(request, path=None):
    """
    Return {language code: absolute URL} for a page in every site language.

    `path` defaults to the page being served. The query string is never carried
    over: a search query or a tracking parameter must not become part of the
    canonical address.
    """
    path = path or request.path
    origin = site_origin(request)
    return {
        code: f'{origin}{translate_url(path, code)}'
        for code, _name in settings.LANGUAGES
    }
