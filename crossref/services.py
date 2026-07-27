"""
Crossref deposit helpers.

Nothing in here talks to Crossref on its own — `submit_batch` is only ever
called from the admin approval action, never from the cron command.
"""

import re
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from core.site_config import ISSN_RE, clean_value, load_site_config

DEPOSIT_PATH = '/servlet/deposit'
RESULT_PATH = '/servlet/submissionDownload'

BASE_URLS = {
    'sandbox': 'https://test.crossref.org',
    'production': 'https://doi.crossref.org',
}

# Landing pages Crossref could never resolve; refuse to deposit these.
UNREACHABLE_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', '::1', 'testserver'}

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')


class CrossrefError(Exception):
    """Raised when a deposit cannot be built or sent."""


def get_site_config():
    return load_site_config(clean=True)


def get_environment():
    env = (getattr(settings, 'CROSSREF_ENVIRONMENT', '') or 'sandbox').lower()
    return env if env in BASE_URLS else 'sandbox'


def get_base_url(environment=None):
    return BASE_URLS[environment or get_environment()]


def get_credentials():
    user = getattr(settings, 'CROSSREF_USERNAME', '') or ''
    password = getattr(settings, 'CROSSREF_PASSWORD', '') or ''
    if not user or not password:
        raise CrossrefError(
            "CROSSREF_USERNAME / CROSSREF_PASSWORD are not set. Add them to .env "
            "(see .env.example) and restart the server."
        )
    return user, password


def get_doi_prefix(site_config=None):
    site_config = site_config if site_config is not None else get_site_config()
    prefix = site_config.get('doi_prefix', '') or (getattr(settings, 'CROSSREF_DOI_PREFIX', '') or '').strip()
    if not prefix:
        raise CrossrefError(
            "No DOI prefix configured. Add a 'doi_prefix' row in Default Settings "
            "(e.g. 10.64964)."
        )
    if not prefix.startswith('10.'):
        raise CrossrefError(f"DOI prefix {prefix!r} does not look like a Crossref prefix (10.xxxxx).")
    return prefix


def get_site_base_url():
    base = (getattr(settings, 'SITE_BASE_URL', '') or '').strip().rstrip('/')
    if not base:
        raise CrossrefError("SITE_BASE_URL is not set. Add it to .env (see .env.example).")
    host = (urlparse(base).hostname or '').lower()
    if host in UNREACHABLE_HOSTS:
        raise CrossrefError(
            f"SITE_BASE_URL points at {host!r}. Crossref must be able to reach the landing "
            "page from the public internet — set it to the live domain."
        )
    return base


def get_depositor_email(site_config):
    """
    Find a real address for the depositor.

    The site's contact_email setting is free text ("Email: x@y.uz" inside
    markup), so pull the address out of it rather than depositing the sentence.
    """
    candidates = [
        getattr(settings, 'CROSSREF_DEPOSIT_EMAIL', ''),
        site_config.get('contact_email', ''),
        site_config.get('submission_email', ''),
    ]
    for candidate in candidates:
        match = EMAIL_RE.search(clean_value(candidate))
        if match:
            return match.group(0)
    raise CrossrefError(
        "No depositor email address found. Set CROSSREF_DEPOSIT_EMAIL in .env, "
        "or put a valid address in the 'contact_email' Default setting."
    )


PRINT_WORDS = ('print', 'bosma', 'печат')
ONLINE_WORDS = ('online', 'electronic', 'elektron', 'onlayn', 'электрон')


def get_issns(site_config):
    """
    Return [(issn, media_type), …] for the journal. Crossref rejects journal
    deposits with no ISSN at all, and accepts one element per media type.

    The setting *name* is only a hint. A journal with a single print ISSN often
    has it entered under both keys, with the text itself saying "Print ISSN:
    3060-4559" — so when the value says which kind it is, believe the value.
    Identical numbers are collapsed, otherwise Crossref sees the same ISSN
    declared as two different media types.
    """
    found = {}
    for key, default_media_type in (('issn_print', 'print'), ('issn_online', 'electronic')):
        raw = site_config.get(key, '')
        match = ISSN_RE.search(raw)
        if not match:
            continue
        lowered = raw.lower()
        if any(word in lowered for word in PRINT_WORDS):
            media_type = 'print'
        elif any(word in lowered for word in ONLINE_WORDS):
            media_type = 'electronic'
        else:
            media_type = default_media_type
        # First writer wins, so an explicit label is not overwritten by a guess.
        found.setdefault(match.group(0).upper(), media_type)

    if not found:
        raise CrossrefError(
            "No ISSN configured. Crossref requires an ISSN for journal deposits — add "
            "an 'issn_print' or 'issn_online' row in Default Settings (format 1234-5678)."
        )
    return sorted(found.items())


def build_resource_url(article, base_url=None):
    return f"{base_url or get_site_base_url()}{article.get_absolute_url()}"


def build_doi(article, prefix, taken):
    """
    Mint a stable DOI for an article: <prefix>/comp.<year>.<zero-padded id>.

    `taken` is the set of DOIs already in use (existing articles + DOIs proposed
    earlier in this same run); a collision gets a -2, -3, … suffix.
    """
    year = article.publication_date.year if article.publication_date else timezone.now().year
    candidate = f"{prefix}/comp.{year}.{article.pk:04d}"
    if candidate not in taken:
        return candidate
    n = 2
    while f"{candidate}-{n}" in taken:
        n += 1
    return f"{candidate}-{n}"


def article_title(article):
    """
    Resolve an article's title without depending on the active language.

    `article.title` is a modeltranslation field, so it returns whatever language
    happens to be active — the cron process and the admin see different values,
    and an article with no Uzbek translation reads back empty. Walk the language
    columns in a fixed order so a deposit is reproducible.
    """
    codes = [settings.LANGUAGE_CODE] + [c for c, _ in settings.LANGUAGES if c != settings.LANGUAGE_CODE]
    for code in codes:
        title = clean_value(getattr(article, f'title_{code}', '') or '')
        if title:
            return title
    return clean_value(getattr(article, 'title', '') or '')


# Stripped before splitting: an honorific is not a surname, and surname-first
# splitting would otherwise deposit "Dr." as the author's family name.
HONORIFICS = {'dr', 'prof', 'mr', 'mrs', 'ms', 'phd', 'assoc', 'akad', 'prof.dr'}


def split_authors(raw, surname_first=None):
    """
    Split a free-text authors string into given/surname pairs.

    Uzbek names are written surname first — "Axmedova Aziza Komilovna" is
    surname Axmedova, given name Aziza, patronymic Komilovna — and that is how
    this journal stores them. Western order (given name first) is available via
    CROSSREF_AUTHOR_NAME_ORDER=given-first for journals that need it.
    """
    if surname_first is None:
        order = (getattr(settings, 'CROSSREF_AUTHOR_NAME_ORDER', '') or 'surname-first').lower()
        surname_first = order != 'given-first'

    if not raw:
        return []
    names = [n.strip() for n in clean_value(raw).replace(';', ',').split(',') if n.strip()]
    result = []
    for name in names:
        bits = name.split()
        while len(bits) > 1 and bits[0].lower().strip('.') in HONORIFICS:
            bits = bits[1:]
        name = ' '.join(bits)
        if len(bits) < 2:
            result.append({'given': '', 'surname': name})
        elif surname_first:
            result.append({'given': ' '.join(bits[1:]), 'surname': bits[0]})
        else:
            result.append({'given': ' '.join(bits[:-1]), 'surname': bits[-1]})
    return result


def make_batch_id():
    return f"{timezone.now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:8]}"


def build_deposit_xml(entries, batch_id=None, site_config=None):
    """
    Render the Crossref deposit XML.

    `entries` is a list of (article, doi, resource_url) tuples. Articles are
    grouped by their parent Issue, which is what the Crossref schema expects.
    """
    # Re-clean even a caller-supplied config: nothing with markup in it may
    # reach the deposit, and clean_value is a no-op on already-plain text.
    site_config = {k: clean_value(v) for k, v in (
        site_config if site_config is not None else get_site_config()
    ).items()}

    groups, order = {}, []
    for article, doi, resource_url in entries:
        if article.issue_id not in groups:
            groups[article.issue_id] = {'issue': article.issue, 'articles': []}
            order.append(article.issue_id)
        groups[article.issue_id]['articles'].append({
            'title': article_title(article),
            'doi': doi,
            'publication_date': article.publication_date,
            'absolute_url': resource_url,
            'authors_list': split_authors(article.authors),
        })

    context = {
        'issns': get_issns(site_config),
        'batch_id': batch_id or make_batch_id(),
        'timestamp': f"{timezone.now():%Y%m%d%H%M%S}",
        'depositor_name': (
            site_config.get('crossref_registrant') or site_config.get('publisher')
            or site_config.get('editor_in_chief') or 'Journal Editor'
        ),
        'depositor_email': get_depositor_email(site_config),
        'registrant': (
            site_config.get('crossref_registrant') or site_config.get('publisher')
            or site_config.get('site_title') or 'Journal Publisher'
        ),
        'journal_title': site_config.get('site_title') or 'Journal',
        'issue_groups': [groups[k] for k in order],
    }
    return render_to_string('crossref/deposit.xml', context)


def submit_batch(batch, timeout=60):
    """
    POST a batch to Crossref. Returns (ok, message) and never raises on a
    network error — the caller records the message on the batch instead.
    """
    import requests

    try:
        user, password = get_credentials()
    except CrossrefError as exc:
        return False, str(exc)

    url = f"{get_base_url(batch.environment)}{DEPOSIT_PATH}"
    try:
        response = requests.post(
            url,
            data={'operation': 'doMDUpload', 'login_id': user, 'login_passwd': password},
            files={'fname': (f"{batch.batch_id}.xml", batch.xml.encode('utf-8'), 'application/xml')},
            timeout=timeout,
        )
    except Exception as exc:
        return False, f"Network error contacting {url}: {exc}"

    body = (response.text or '').strip()
    snippet = body[:2000]
    if response.status_code != 200:
        return False, f"HTTP {response.status_code} from Crossref: {snippet}"
    if re.search(r'\berror\b', body, re.IGNORECASE) and 'SUCCESS' not in body.upper():
        return False, f"Crossref rejected the submission: {snippet}"
    return True, f"Submitted to {url}. Response: {snippet}"


def check_batch(batch, timeout=60):
    """
    Poll Crossref for a submitted batch's result.

    Returns (state, message) where state is one of 'registered', 'failed',
    'pending' (still processing) or 'unknown'.
    """
    import requests

    try:
        user, password = get_credentials()
    except CrossrefError as exc:
        return 'unknown', str(exc)

    url = f"{get_base_url(batch.environment)}{RESULT_PATH}"
    try:
        response = requests.get(
            url,
            params={'usr': user, 'pwd': password, 'doi_batch_id': batch.batch_id, 'type': 'result'},
            timeout=timeout,
        )
    except Exception as exc:
        return 'unknown', f"Network error contacting {url}: {exc}"

    body = (response.text or '').strip()
    if response.status_code != 200:
        return 'unknown', f"HTTP {response.status_code}: {body[:1000]}"
    if not body or 'not found' in body.lower():
        return 'pending', "Crossref has no result for this batch yet."

    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return 'unknown', f"Could not parse Crossref response: {body[:1000]}"

    success = failure = 0
    for node in root.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if tag == 'batch_data':
            success = int(node.findtext('.//{*}success_count') or 0)
            failure = int(node.findtext('.//{*}failure_count') or 0)
        elif tag == 'record_diagnostic':
            if (node.get('status') or '').lower() == 'success':
                success += 1
            elif (node.get('status') or '').lower() in ('failure', 'error'):
                failure += 1

    if failure:
        return 'failed', f"{failure} record(s) failed, {success} succeeded. Response: {body[:2000]}"
    if success:
        return 'registered', f"{success} record(s) registered. Response: {body[:2000]}"
    return 'pending', f"No counts in response yet: {body[:1000]}"
