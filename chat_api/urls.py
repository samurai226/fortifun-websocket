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

# Configuration du routeur pour les viewsets
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'matches', MatchViewSet, basename='match')

urlpatterns = [
    path('admin/', admin.site.urls),
    
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