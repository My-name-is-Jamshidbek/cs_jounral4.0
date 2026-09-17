"""
Serve the site from one host only.

The site answered on www.jurnal-komparativistika.uz as well as the bare domain,
with every page on both declaring itself canonical. Google saw two complete
copies of the site and picked between them itself, which Search Console reported
as "Google chose a different canonical than the user". Requests for the www host
are sent to the SITE_BASE_URL host with a permanent redirect.
"""

from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        base = (getattr(settings, 'SITE_BASE_URL', '') or '').strip().rstrip('/')
        canonical_host = (urlsplit(base).hostname or '').lower()
        host = request.get_host().split(':', 1)[0].lower()
        # Only the www alias is redirected. Any other host (localhost, the test
        # client, a staging server) is left alone rather than bounced to production.
        if canonical_host and host == f'www.{canonical_host}':
            return HttpResponsePermanentRedirect(f'{base}{request.get_full_path()}')
        return self.get_response(request)
