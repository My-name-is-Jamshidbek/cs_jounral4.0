from django.shortcuts import render
from .models import Subscribe


def index(request):
    """
    Display subscribe page with dynamic content from Subscribe model.
    """
    # Get main content items for the main subscription section
    main_content = Subscribe.objects.filter(type='main').order_by('created_at')

    # Get sidebar content items for the sidebar section
    sidebar_content = Subscribe.objects.filter(type='sidebar').order_by('created_at')

    context = {
        'main_content': main_content,
        'sidebar_content': sidebar_content,
    }

    return render(request, 'subscribe.html', context)
