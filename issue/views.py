from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
import json

from django.utils.datetime_safe import datetime

from issue.models import Issue, JournalIssue


def current_issue(request):
    """Display the current/latest journal issue with articles."""
    # Get the most recent published issue
    current_issue = Issue.objects.order_by('-publication_date').first()

    # Get articles for the current issue
    articles = []
    if current_issue:
        articles = JournalIssue.objects.filter(
            issue=current_issue
        ).order_by('id')  # You can change ordering as needed

    context = {
        'current_issue': current_issue,
        'articles': articles,
    }

    return render(request, 'current_issue.html', context)


def item_issue(request, pk):
    """Display the current/latest journal issue with articles."""
    # Get the most recent published issue
    current_issue = get_object_or_404(Issue, pk=pk)
    # Get articles for the current issue
    articles = []
    if current_issue:
        articles = JournalIssue.objects.filter(
            issue=current_issue
        ).order_by('id')  # You can change ordering as needed

    context = {
        'current_issue': current_issue,
        'articles': articles,
    }

    return render(request, 'current_issue.html', context)


def all_issues(request):
    """Display all journal issues with their articles organized by year and decade."""
    # Get all issues ordered by publication date (newest first)
    issues = Issue.objects.all().order_by('publication_date')

    # Organize issues by year and decade for the JavaScript frontend
    issues_by_year = {}
    decades_dict = {}

    for issue in issues:
        year = issue.publication_date.year
        decade = f"{(year // 10) * 10}s"

        # Track years by decade for UI navigation
        if decade not in decades_dict:
            decades_dict[decade] = []
        if year not in decades_dict[decade]:
            decades_dict[decade].append(year)

        # Group issues by year
        if year not in issues_by_year:
            issues_by_year[year] = []

        # Format date as "Month Year"
        formatted_date = issue.publication_date.strftime('%B %Y')

        # Generate the URL for this issue using Django's reverse
        issue_url = reverse('item_issue', kwargs={'pk': issue.pk})

        issue_data = {
            'volume': issue.volume,
            'issue': issue.issue_number,
            'date': formatted_date,
            'title': issue.title or "",
            'id': issue.id,
            'url': issue_url,
            'description': issue.description or "",
            'cover_image': issue.cover_image.url if issue.cover_image else None
        }
        issues_by_year[year].append(issue_data)

    # Sort years within each decade
    for decade in decades_dict:
        decades_dict[decade] = sorted(decades_dict[decade], reverse=True)

    context = {
        'issues_data': json.dumps(issues_by_year),
        'decades_data': json.dumps(decades_dict),
        'current_year': datetime.now().year
    }

    return render(request, 'all_issues.html', context)