# chat_api/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from conversations.views import ConversationViewSet, MessageViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from django.http import JsonResponse
from matching.views import MatchViewSet
import os
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
import threading
import random
import boto3
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import django

# Configuration du routeur pour les viewsets
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'matches', MatchViewSet, basename='match')

DEFAULT_SEED_TOKEN = os.getenv('DEFAULT_SEED_TOKEN', 'seed-3f3e7d8d-7d8b-4a0a-9f7d-2a1c6f8b1d92')

# Temporary token-protected seeding endpoint
@api_view(['POST', 'GET'])
@permission_classes([permissions.AllowAny])
def seed_users(request):
    provided = request.headers.get('X-Seed-Token') or request.GET.get('token')
    expected = os.getenv('SEED_TOKEN', DEFAULT_SEED_TOKEN)
    if not expected or provided != expected:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    try:
        limit = int(request.GET.get('limit', '250'))
        # Only run on POST; GET just confirms route
        if request.method == 'POST':
            # Run seeding in a background thread to avoid request timeout on free plan
            def run_seed():
                call_command('create_profiles_with_images', csv_file='seed_assets/profiles/users.csv', s3_folder='profil/', limit=limit)
            threading.Thread(target=run_seed, daemon=True).start()
            return JsonResponse({'detail': 'seed_started_async', 'limit': limit}, status=202)
        return JsonResponse({'detail': 'ok', 'limit': limit})
    except Exception as e:
        return JsonResponse({'detail': 'error', 'error': str(e)}, status=500)

# Token-protected endpoint to assign random S3 images to users without photo
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def assign_missing_photos(request):
    provided = request.headers.get('X-Seed-Token') or request.GET.get('token')
    expected = os.getenv('SEED_TOKEN', DEFAULT_SEED_TOKEN)
    if not expected or provided != expected:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    try:
        limit = request.GET.get('limit')
        limit = int(limit) if limit and limit.isdigit() else None
        # Run in background to avoid timeout on free plan
        def run_assign():
            call_command('assign_s3_images_to_users', limit=limit)
        threading.Thread(target=run_assign, daemon=True).start()
        return JsonResponse({'detail': 'assign_started_async', 'limit': limit}, status=202)
    except Exception as e:
        return JsonResponse({'detail': 'error', 'error': str(e)}, status=500)

# Token-protected DB ping endpoint
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def db_ping(request):
    provided = request.headers.get('X-Seed-Token') or request.GET.get('token')
    expected = os.getenv('SEED_TOKEN', DEFAULT_SEED_TOKEN)
    if not expected or provided != expected:
        return JsonResponse({'detail': 'forbidden'}, status=403)
    try:
        with connection.cursor() as cursor:
            cursor.execute("select version(), current_database()")
            version, current_db = cursor.fetchone()
        User = get_user_model()
        user_count = User.objects.count()
        return JsonResponse({
            'detail': 'ok',
            'db': current_db,
            'version': version,
            'user_count': user_count,
        })
    except Exception as e:
        return JsonResponse({'detail': 'error', 'error': str(e)}, status=500)

# CORS test endpoint
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def cors_test(request):
    """Test CORS configuration"""
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    return JsonResponse({
        'status': 'cors_working',
        'message': 'CORS configuration is working',
        'timestamp': timezone.now().isoformat(),
    })

# Health check endpoint
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
    # CORS test endpoint
    path('cors-test/', cors_test),
    path('cors-test', cors_test),
    # Health check endpoint
    path('health/', health_check),
    path('health', health_check),
    # Temporary seeding URLs (with and without trailing slash)
    path('api/v1/admin/seed-users/', seed_users),
    path('api/v1/admin/seed-users', seed_users),
    path('api/v1/admin/assign-missing-photos/', assign_missing_photos),
    path('api/v1/admin/assign-missing-photos', assign_missing_photos),
    # DB ping URLs
    path('api/v1/admin/db-ping/', db_ping),
    path('api/v1/admin/db-ping', db_ping),
    
    # API URLs
    path('api/v1/', include([
        # Router for conversations and matches
        path('', include(router.urls)),
        
        # Nested routes for messages
        path('conversations/<int:conversation_pk>/messages/', include([
            path('', MessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='message-list'),
            path('<int:pk>/', MessageViewSet.as_view({
                'get': 'retrieve', 
                'put': 'update', 
                'patch': 'partial_update', 
                'delete': 'destroy'
            }), name='message-detail'),
            path('<int:pk>/mark_read/', MessageViewSet.as_view({'post': 'mark_read'}), name='message-mark-read'),
        ])),
        
        # Appwrite Authentication & User Management
        path('accounts/', include('accounts.urls')),
        
        # Matching & User Discovery
        path('matching/', include('matching.urls')),
    ])),
]

# Sert les média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)