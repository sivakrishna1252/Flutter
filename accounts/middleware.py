from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from rest_framework import status

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            last_activity = request.user.last_activity
            
            # Update last activity if more than 1 minute has passed (to avoid database spam)
            if not last_activity or (now - last_activity) > timedelta(minutes=1):
                request.user.last_activity = now
                request.user.save(update_fields=['last_activity'])

        response = self.get_response(request)
        return response
