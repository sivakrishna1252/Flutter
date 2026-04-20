from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from rest_framework import status

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply inactivity check to app API users
        path = request.path
        if path.startswith('/api/') and not (path.startswith('/api/schema/') or path.startswith('/api/auth/')):
            if request.user.is_authenticated:
                now = timezone.now()
                last_activity = request.user.last_activity
                
                # Check if inactive for more than 5 minutes
                if last_activity and (now - last_activity) > timedelta(minutes=5):
                    return JsonResponse(
                        {"error": "Session expired. Please login again."},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Update last activity
                if not last_activity or (now - last_activity) > timedelta(minutes=1):
                    request.user.last_activity = now
                    request.user.save(update_fields=['last_activity'])
        else:
            # For non-API or Auth/Swagger, just update activity without blocking
            if request.user.is_authenticated:
                now = timezone.now()
                if not request.user.last_activity or (now - request.user.last_activity) > timedelta(minutes=1):
                    request.user.last_activity = now
                    request.user.save(update_fields=['last_activity'])

        response = self.get_response(request)
        return response
