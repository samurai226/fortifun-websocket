# chat_api/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from conversations.views import ConversationViewSet, MessageViewSet
from matching.views import MatchViewSet

# Configuration du routeur pour les viewsets
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'matches', MatchViewSet, basename='match')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API URLs
    path('api/v1/', include([
        # Router
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
        
        # Auth & Users
        path('auth/', include('accounts.urls')),
        
        # Matching
        path('matching/', include('matching.urls')),
    ])),
]

# Sert les média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)