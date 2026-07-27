"""
Reading the Default settings table.

Two things make this less trivial than a dict comprehension:

* `Default.name` is registered with modeltranslation, so a row whose Uzbek tab
  was left blank reads back as an empty key and silently disappears from the
  config. A settings key is not translatable content, so resolve it across the
  language columns instead.
* `Default.value` is a CKEditor field, so values arrive wrapped in markup. Some
  templates want that markup; anything used as metadata (ISSN, email, titles in
  meta tags) wants plain text. Hence `clean_value`, applied at the point of use
  rather than to the whole dict.
"""

import html
import re

from django.conf import settings
from django.utils.html import strip_tags

from .models import Default

ISSN_RE = re.compile(r'\d{4}-\d{3}[\dXx]')


def clean_value(raw):
    """Flatten a CKEditor value to plain text, decoding the entities it leaves behind."""
    text = html.unescape(strip_tags(raw or ''))
    return text.replace('\xa0', ' ').strip()


def extract_issn(raw):
    """
    Pull the bare ISSN out of a setting.

    The value is usually written for humans ("Print ISSN: 3060-4559"), but
    citation_issn must carry the number alone or Google Scholar cannot match it.
    """
    match = ISSN_RE.search(clean_value(raw))
    return match.group(0).upper() if match else ''


def config_key(row):
    """Read a Default row's key from whichever language column it was typed into."""
    for field in ['name'] + [f'name_{code}' for code, _ in settings.LANGUAGES]:
        key = clean_value(getattr(row, field, '') or '')
        if key:
            return key
    return ''


def load_site_config(clean=False):
    """
    Return {key: value} for every Default row that has a usable key.

    `clean=False` keeps the CKEditor markup, which the templates that render
    rich text depend on. `clean=True` strips it, for metadata use.
    """
    config = {}
    for row in Default.objects.all():
        key = config_key(row)
        if key:
            config[key] = clean_value(row.value) if clean else row.value
    return config
