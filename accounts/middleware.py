from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from rest_framework import status

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply inactivity check to API endpoints, excluding swagger docs
        is_api_path = request.path.startswith('/api/')
        is_swagger_path = request.path.startswith('/api/schema/')
        
        if not is_api_path or is_swagger_path:
            return self.get_response(request)

        if request.user.is_authenticated:
            now = timezone.now()
            last_activity = request.user.last_activity
            
            # Check if user has been inactive for more than 10 minutes
            if last_activity and (now - last_activity) > timedelta(minutes=10):
                # Optionally: here you could also blacklist tokens if using a more complex setup
                # For now, we just return 401 to force logout on the frontend
                return JsonResponse(
                    {"error": "Session expired due to inactivity. Please login again."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Update last activity if more than 1 minute has passed (to avoid database spam)
            if not last_activity or (now - last_activity) > timedelta(minutes=1):
                request.user.last_activity = now
                request.user.save(update_fields=['last_activity'])

        response = self.get_response(request)
        return response
