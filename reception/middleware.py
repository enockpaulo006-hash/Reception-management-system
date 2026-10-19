from django.shortcuts import redirect
from django.urls import reverse


class FirstRunSetupMiddleware:
    """Send an unconfigured installation to its one-time setup page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.contrib.auth.models import User

        setup_url = reverse("setup")
        if not User.objects.exists() and request.path != setup_url:
            return redirect(setup_url)
        return self.get_response(request)
