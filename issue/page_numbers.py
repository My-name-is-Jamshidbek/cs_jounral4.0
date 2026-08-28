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

# A printed page number sits alone on its line. Bounded to four digits: a longer
# run of digits is a year, a UDC code or a phone number, not a page.
PAGE_LINE = re.compile(r'^(\d{1,4})$')

# How many lines from the top of a page to look at. The header is one or two
# lines, so anything further down is body text that merely starts with a number.
HEADER_LINES = 4


def printed_page_number(page):
    """Return the page number printed in this PDF page's header, or None."""
    lines = [line.strip() for line in (page.extract_text() or '').split('\n') if line.strip()]
    for line in lines[:HEADER_LINES]:
        match = PAGE_LINE.match(line)
        if match:
            return int(match.group(1))
    return None


def page_range(path):
    """
    Return (first, last, problem) for one PDF.

    `problem` is None when the range was read *and verified*: the number of
    pages between first and last must equal the number of pages in the file.
    A page range ends up in Crossref and in every citation Google Scholar
    builds, so a PDF that fails the check yields a problem rather than a guess.
    """
    import pypdf

    try:
        reader = pypdf.PdfReader(path)
    except Exception as exc:
        return None, None, f"cannot read the PDF ({exc})"

    count = len(reader.pages)
    if not count:
        return None, None, "PDF has no pages"

    first = printed_page_number(reader.pages[0])
    last = printed_page_number(reader.pages[-1])
    if first is None or last is None:
        return None, None, "no page number printed in the header"
    if last < first:
        return None, None, f"last page {last} is before first page {first}"
    if last - first + 1 != count:
        return None, None, (f"printed range {first}-{last} covers {last - first + 1} pages "
                            f"but the file has {count}")
    return first, last, None
