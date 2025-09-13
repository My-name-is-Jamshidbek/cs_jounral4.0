from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages

from core.models import Joining
from issue.models import JournalIssue, Issue


@require_POST
def join(request):
    """
    Handle the joining request.
    """
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    email = request.POST.get('email')
    institution = request.POST.get('institution')
    country = request.POST.get('country')

    try:
        Joining.objects.create(first_name=first_name, last_name=last_name, email=email,
                               institution=institution, country=country)
        messages.success(request, f'Thank you {first_name}! You have successfully joined our mailing list.')
    except Exception as e:
        messages.error(request, 'Sorry, there was an error processing your request. Please try again.')

    return redirect('index')  # Redirect to the home page after successful join

def index(request):
    # Dynamic home page: fetch articles for each tab and sidebar flags
    latest_articles = JournalIssue.objects.order_by('-publication_date')[:10]
    most_read_articles = JournalIssue.objects.order_by('-views')[:10]
    latest_issue = Issue.objects.order_by('-publication_date').first()
    context = {
        'latest_articles': latest_articles,
        'most_read_articles': most_read_articles,
        'latest_issue': latest_issue,
        'show_alerts': True,
        'show_publisher': True,
        'show_free_content': True,
        'show_news': True,
    }
    return render(request, 'journal_home.html', context)
