"""
Fill in each article's page range by reading it out of the article's own PDF.

The parsing lives in issue/page_numbers.py. Nothing is written unless the range
agrees with the PDF itself, because a page range ends up in Crossref and in
every citation Google Scholar builds: an article whose PDF fails that check is
reported for manual entry rather than filled in with a guess.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from crossref.console import force_utf8
from issue.models import JournalIssue
from issue.page_numbers import page_range


class Command(BaseCommand):
    help = "Fill in first_page/last_page for articles by reading their PDFs."

    def add_arguments(self, parser):
        parser.add_argument('--issue', type=int, default=None,
                            help="Only articles belonging to this Issue id.")
        parser.add_argument('--limit', type=int, default=0,
                            help="Process at most N articles (0 = no limit).")
        parser.add_argument('--overwrite', action='store_true',
                            help="Also replace page numbers that are already set.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Print what would be written without saving.")

    def handle(self, *args, **options):
        force_utf8(self.stdout, self.stderr)
        try:
            import pypdf  # noqa: F401
        except ImportError:
            raise CommandError(
                "pypdf is not installed. Run: venv/bin/pip install pypdf"
            )

        articles = JournalIssue.objects.exclude(file='').exclude(file__isnull=True)
        if not options['overwrite']:
            articles = articles.filter(Q(first_page='') | Q(first_page__isnull=True))
        if options['issue']:
            articles = articles.filter(issue_id=options['issue'])
        articles = articles.order_by('issue_id', 'pk')
        if options['limit']:
            articles = articles[:options['limit']]

        articles = list(articles)
        if not articles:
            self.stdout.write("No articles need page numbers.")
            return

        written = failed = 0
        for article in articles:
            try:
                path = article.file.path
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  #{article.pk}: no readable file ({exc})"))
                failed += 1
                continue

            first, last, problem = page_range(path)
            if problem:
                self.stdout.write(self.style.WARNING(f"  #{article.pk}: {problem} - {article.file.name}"))
                failed += 1
                continue

            self.stdout.write(f"  #{article.pk}: {first}-{last}")
            if options['dry_run']:
                continue
            article.first_page = str(first)
            article.last_page = str(last)
            article.save(update_fields=['first_page', 'last_page'])
            written += 1

        if options['dry_run']:
            self.stdout.write(self.style.NOTICE(
                f"[dry-run] {len(articles) - failed} article(s) would be filled in, "
                f"{failed} need manual entry."
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            f"{written} article(s) updated, {failed} need manual entry in the admin."
        ))
