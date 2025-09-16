# accounts/urls.py

from django.urls import path
from .views import (
    UserDetailView,
    AppwriteUserProfileView, appwrite_webhook, sync_appwrite_profile,
    RegisterView, LoginView, UsersMeView, upload_profile_picture, upload_message_attachment
)

urlpatterns = [
    # Auth endpoints for Flutter (JWT)
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login', LoginView.as_view(), name='auth-login'),
    # Current user profile
    path('users/me', UsersMeView.as_view(), name='users-me'),
    
    # Core Appwrite integration endpoints
    path('appwrite/profile/', AppwriteUserProfileView.as_view(), name='appwrite-user-profile'),
    path('appwrite/webhook/', appwrite_webhook, name='appwrite-webhook'),
    path('appwrite/sync/', sync_appwrite_profile, name='sync-appwrite-profile'),
    
    # Utility endpoint (for admin/legacy purposes)
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # Simple file upload endpoints used by Flutter
    path('files/profile-picture', upload_profile_picture, name='upload-profile-picture'),
    path('files/message-attachment', upload_message_attachment, name='upload-message-attachment'),
]