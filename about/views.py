from django.shortcuts import render, get_object_or_404

from about.models import About


def about(request, pk):
    """
    Render the about page with static content.
    """
    about = get_object_or_404(About, id=pk)
    return render(request, 'about.html', {'about': about})