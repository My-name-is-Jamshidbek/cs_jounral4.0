from django.shortcuts import render, get_object_or_404

from core.models import Default
from submit.models import Permission


def permissions(request, pk):
    """
    Render the permissions page with static content.
    """
    if pk == 1:
        permission = Permission.objects.first()
    else:
        permission = get_object_or_404(Permission, pk=pk)

    all_permissions = Permission.objects.all()
    return render(request, 'sumbit/permissions/index.html', {'permissions': all_permissions, 'permission': permission})

def submission(request):
    """
    Render the submission guidelines page.
    """
    content_submission = get_object_or_404(Default, name="submission")
    return render(request, 'sumbit/submission.html', {"submission": content_submission})

def permission(request):
    """
    Render the submission guidelines page.
    """
    content_submission = get_object_or_404(Default, name="permission")
    return render(request, 'sumbit/submission.html', {"submission": content_submission})