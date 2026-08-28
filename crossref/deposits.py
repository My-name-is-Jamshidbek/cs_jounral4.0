"""
Deposit orchestration: choosing articles, freezing a batch, sending it, and
recording the result.

`services.py` builds the XML and talks HTTP; this module is the workflow around
it. Both entry points — the review-first `queue_doi_deposits` and the unattended
`register_dois` — go through the same functions here, so they can never disagree
about which articles are eligible, what DOI each one gets, or what is checked
before anything irreversible is sent.
"""

import xml.etree.ElementTree as ET

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from crossref.models import DepositBatch, DepositItem
from crossref.services import (
    article_title, author_problems, build_deposit_xml, build_doi,
    build_resource_url, get_doi_prefix, get_environment, get_site_base_url,
    get_site_config, make_batch_id, submit_batch,
)


def article_deposit_problem(article):
    """
    Return why this article cannot be deposited, or None if it is fine.

    Crossref validates a submission as a single document, so one bad record
    rejects the whole batch. Everything checkable locally is checked here.
    """
    if not article.publication_date:
        return "no publication date"
    # Crossref rejects an empty <title>, and a DOI is permanent — better to
    # leave an article un-deposited than to register it untitled.
    if not article_title(article):
        return "no title in any language"
    problems = author_problems(article.authors)
    if problems:
        return '; '.join(problems)
    return None


def collect_deposit_entries(issue_id=None, limit=0, site_config=None, article_ids=None):
    """
    Pick every article still waiting for a DOI and mint one for each.

    Returns (entries, skipped): entries is [(article, doi, resource_url)] ready
    for `build_deposit_xml`, skipped is [(article, reason)].
    """
    from issue.models import JournalIssue

    site_config = site_config if site_config is not None else get_site_config()
    prefix = get_doi_prefix(site_config)
    base_url = get_site_base_url()

    # Articles already sitting in a batch that is pending or in flight must not
    # be queued a second time.
    in_flight = DepositItem.objects.filter(
        batch__status__in=[DepositBatch.PENDING, DepositBatch.SUBMITTED],
        status__in=[DepositItem.PENDING, DepositItem.DEPOSITED],
    ).values_list('article_id', flat=True)

    # doi is null=True *and* blank=True, so cover the empty-string case too.
    articles = (
        JournalIssue.objects
        .filter(Q(doi__isnull=True) | Q(doi__exact=''))
        .exclude(pk__in=in_flight)
        .select_related('issue')
        .order_by('issue_id', 'pk')
    )
    if issue_id:
        articles = articles.filter(issue_id=issue_id)
    if article_ids is not None:
        articles = articles.filter(pk__in=article_ids)
    if limit:
        articles = articles[:limit]

    taken = set(
        JournalIssue.objects.exclude(doi__isnull=True).exclude(doi__exact='')
        .values_list('doi', flat=True)
    )
    taken |= set(
        DepositItem.objects
        .exclude(batch__status__in=[DepositBatch.FAILED, DepositBatch.CANCELLED])
        .values_list('proposed_doi', flat=True)
    )

    entries, skipped = [], []
    for article in articles:
        reason = article_deposit_problem(article)
        if reason:
            skipped.append((article, reason))
            continue
        doi = build_doi(article, prefix, taken)
        taken.add(doi)
        entries.append((article, doi, build_resource_url(article, base_url)))
    return entries, skipped


def collect_update_entries(issue_id=None, limit=0, article_ids=None, resource_override=None):
    """
    Gather articles that already have a DOI, to re-send their current metadata.

    Crossref treats a deposit of a DOI it already knows as an update, so this is
    how a correction reaches a registered record — page numbers added after the
    fact, a fixed title, or a duplicate DOI redirected at the surviving article.

    `resource_override` maps article pk to a landing page URL, for the duplicate
    case where a DOI must resolve somewhere other than its own article.
    """
    from issue.models import JournalIssue

    base_url = get_site_base_url()

    articles = (
        JournalIssue.objects
        .exclude(doi__isnull=True).exclude(doi__exact='')
        .select_related('issue')
        .order_by('issue_id', 'pk')
    )
    if issue_id:
        articles = articles.filter(issue_id=issue_id)
    if article_ids is not None:
        articles = articles.filter(pk__in=article_ids)
    if limit:
        articles = articles[:limit]

    entries, skipped = [], []
    for article in articles:
        reason = article_deposit_problem(article)
        if reason:
            skipped.append((article, reason))
            continue
        url = (resource_override or {}).get(article.pk) or build_resource_url(article, base_url)
        entries.append((article, article.doi, url))
    return entries, skipped


def create_batch(entries, skipped=(), environment=None, site_config=None, note='',
                 kind=DepositBatch.NEW):
    """Freeze `entries` into a pending DepositBatch together with its XML."""
    environment = environment or get_environment()
    batch_id = make_batch_id()
    xml = build_deposit_xml(entries, batch_id=batch_id, site_config=site_config)

    with transaction.atomic():
        batch = DepositBatch.objects.create(
            batch_id=batch_id, environment=environment, xml=xml,
            status=DepositBatch.PENDING, kind=kind,
        )
        batch.append_log(note or f"Queued with {len(entries)} article(s) for {environment}.")
        if skipped:
            batch.append_log(f"{len(skipped)} article(s) skipped: " +
                             "; ".join(f"#{a.pk} ({r})" for a, r in skipped))
        batch.save(update_fields=['log'])
        DepositItem.objects.bulk_create([
            DepositItem(batch=batch, article=article, proposed_doi=doi, resource_url=url)
            for article, doi, url in entries
        ])
    return batch


def validate_batch(batch):
    """
    Re-check a batch against the live database. Returns a problem string, or
    None when the batch is safe to send.

    The XML is rendered when the batch is queued, so anything that changed since
    then makes it stale.
    """
    from issue.models import JournalIssue

    items = list(batch.items.select_related('article'))
    if not items:
        return "batch has no articles."

    if batch.kind == DepositBatch.UPDATE:
        # An update must re-send each article's own registered DOI. Sending a
        # different one would register a second DOI for the same article rather
        # than correcting the first.
        moved = [i for i in items if i.article.doi != i.proposed_doi]
        if moved:
            return (
                f"{len(moved)} article(s) no longer carry the DOI this batch would update "
                f"(e.g. #{moved[0].article_id} now has {moved[0].article.doi or 'no DOI'}, "
                f"batch has {moved[0].proposed_doi}). Cancel this batch and queue a new one."
            )
    else:
        already = [i for i in items if i.article.doi]
        if already:
            return (
                f"{len(already)} article(s) already have a DOI (e.g. #{already[0].article_id} = "
                f"{already[0].article.doi}). Cancel this batch and queue a new one."
            )

    proposed = [i.proposed_doi for i in items]
    if len(set(proposed)) != len(proposed):
        return "the batch proposes the same DOI for more than one article."

    clash = (
        JournalIssue.objects.filter(doi__in=proposed)
        .exclude(pk__in=[i.article_id for i in items])
        .values_list('doi', flat=True)
    )
    if clash:
        return f"proposed DOI(s) already used by other articles: {', '.join(clash)}."

    # The XML is frozen at queue time but the items are not: deleting an article
    # cascades its item away and leaves the DOI stranded in the XML, which would
    # register a DOI resolving to a deleted page.
    try:
        root = ET.fromstring(batch.xml)
    except ET.ParseError as exc:
        return f"stored XML is not parseable ({exc}). Cancel this batch and queue a new one."
    # iterfind, not iter: the {*} namespace wildcard is an ElementPath feature
    # and iter() would match nothing at all here.
    in_xml = {node.text.strip() for node in root.iterfind('.//{*}doi') if node.text}
    if in_xml != set(proposed):
        orphaned = in_xml - set(proposed)
        detail = f" Stale entries: {', '.join(sorted(orphaned))}." if orphaned else ''
        return (
            "the XML no longer matches this batch's articles — it was rendered before the "
            f"articles changed.{detail} Cancel this batch and queue a new one."
        )
    return None


def approve_and_submit(batch, user=None, actor=None, timeout=60):
    """
    Validate, send and record one batch. Returns (ok, message).

    The admin action and the unattended command both go through here, so an
    automatic deposit passes exactly the checks a human approval does. `user` is
    the approving User (admin only); `actor` names the caller in the log.
    """
    if not batch.is_editable:
        return False, (f"status is '{batch.get_status_display()}', "
                       "only pending batches can be deposited.")

    problem = validate_batch(batch)
    if problem:
        batch.append_log(f"Deposit refused: {problem}")
        batch.save(update_fields=['log'])
        return False, problem

    ok, message = submit_batch(batch, timeout=timeout)
    batch.approved_at = timezone.now()
    if user is not None:
        batch.approved_by = user
    batch.append_log(f"Approved by {actor or user or 'unknown'}. {message}")

    if not ok:
        batch.status = DepositBatch.FAILED
        batch.items.update(status=DepositItem.FAILED)
        batch.save(update_fields=['status', 'approved_at', 'approved_by', 'log'])
        return False, message

    with transaction.atomic():
        for item in batch.items.select_related('article'):
            # Already equal for an update batch, which validate_batch enforces.
            if item.article.doi != item.proposed_doi:
                item.article.doi = item.proposed_doi
                item.article.save(update_fields=['doi'])
            item.status = DepositItem.DEPOSITED
            item.save(update_fields=['status'])
        batch.status = DepositBatch.SUBMITTED
        batch.submitted_at = timezone.now()
        batch.save(update_fields=['status', 'submitted_at', 'approved_at', 'approved_by', 'log'])
    return True, message


def record_batch_result(batch, state, message):
    """
    Apply a `check_batch` outcome to a batch and its items.

    Releasing the DOIs of a rejected batch is the important part: the DOI is
    written to the article at submit time but Crossref only registers it later,
    so a failure would otherwise leave the article showing a DOI that resolves
    nowhere and — worse — looking finished, so every later run skips it forever.
    """
    batch.checked_at = timezone.now()
    batch.append_log(f"Result check: {state} - {message}")

    if state == 'registered':
        batch.status = DepositBatch.REGISTERED
        batch.items.update(status=DepositItem.REGISTERED)
    elif state == 'failed':
        batch.status = DepositBatch.FAILED
        released = 0
        # Only a `new` batch may take its DOIs back. An update batch re-sends
        # DOIs that are already registered and permanent: clearing those would
        # strip live DOIs off the site because a correction was rejected.
        if batch.kind == DepositBatch.NEW:
            for item in batch.items.select_related('article'):
                # Only take back the DOI this batch proposed: an editor may have
                # set a different one by hand in the meantime.
                if item.article.doi == item.proposed_doi:
                    item.article.doi = None
                    item.article.save(update_fields=['doi'])
                    released += 1
        batch.items.update(status=DepositItem.FAILED)
        if released:
            batch.append_log(f"Cleared {released} unregistered DOI(s) from their articles.")
        elif batch.kind == DepositBatch.UPDATE:
            batch.append_log("Update batch: the existing DOIs were left untouched.")

    batch.save(update_fields=['status', 'checked_at', 'log'])
    return batch
