# Step 1: Minimal working configuration
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Minimal health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'message': 'Backend is running'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check),
    path('health', health_check),
]
