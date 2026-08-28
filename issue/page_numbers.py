"""
Reading an article's printed page range out of its own PDF.

Every article PDF carries the issue header on each page, with the printed page
number on its own line directly underneath:

    KOMPARATIVISTIKA (Comparative Studies)        No4 (12)-2026
    7

So the first page of the PDF gives first_page and the last gives last_page.

Deliberately free of Django imports so the parsing can be exercised against a
PDF on its own.
"""

import re
from collections import namedtuple

# A printed page number sits alone on its line. Bounded to four digits: a longer
# run of digits is a year, a UDC code or a phone number, not a page.
PAGE_LINE = re.compile(r'^(\d{1,4})$')

# How many lines from the top of a page to look at. The header is one or two
# lines, so anything further down is body text that merely starts with a number.
HEADER_LINES = 4

# Every article opens with its UDC classification line, in one of several
# spellings ("UOʻK(UDC, УДК):", "UDC (UOʻK, УДК):"). It marks where the article
# itself begins, which is not always the first page of the file: some PDFs were
# split with a few trailing pages of the previous article still attached.
ARTICLE_START = re.compile(r'\b(UDC|УДК)\b', re.IGNORECASE)

# Only look for that marker near the front. Further in, a reference list can
# mention a UDC code and would drag the start of the article with it.
START_SEARCH_PAGES = 8

PageRange = namedtuple('PageRange', 'first last problem leading')


def printed_page_number(page):
    """Return the page number printed in this PDF page's header, or None."""
    lines = [line.strip() for line in (page.extract_text() or '').split('\n') if line.strip()]
    for line in lines[:HEADER_LINES]:
        match = PAGE_LINE.match(line)
        if match:
            return int(match.group(1))
    return None


def article_start_index(reader):
    """Index of the page the article itself starts on, 0 for a clean file."""
    for index, page in enumerate(reader.pages[:START_SEARCH_PAGES]):
        if ARTICLE_START.search(page.extract_text() or ''):
            return index
    return 0


def page_range(path):
    """
    Return PageRange(first, last, problem, leading) for one PDF.

    `problem` is None when the range was read *and verified*: the span from
    first to last must equal the number of pages the article actually occupies.
    A page range ends up in Crossref and in every citation Google Scholar
    builds, so a PDF that fails the check yields a problem rather than a guess.

    `leading` counts pages sitting in front of the article, left over from the
    previous one when the issue PDF was split.
    """
    import pypdf

    def fail(message, leading=0):
        return PageRange(None, None, message, leading)

    try:
        reader = pypdf.PdfReader(path)
    except Exception as exc:
        return fail(f"cannot read the PDF ({exc})")

    if not len(reader.pages):
        return fail("PDF has no pages")

    start = article_start_index(reader)
    count = len(reader.pages) - start

    first = printed_page_number(reader.pages[start])
    last = printed_page_number(reader.pages[-1])
    if first is None or last is None:
        return fail("no page number printed in the header", start)
    if last < first:
        return fail(f"last page {last} is before first page {first}", start)
    if last - first + 1 != count:
        return fail(f"printed range {first}-{last} covers {last - first + 1} pages "
                    f"but the article occupies {count}", start)
    return PageRange(first, last, None, start)
