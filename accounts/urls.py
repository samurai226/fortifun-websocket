# accounts/urls.py

from django.urls import path
from .views import (
    UserDetailView,
    RegisterView, LoginView, UsersMeView, upload_profile_picture, upload_message_attachment,
    set_test_user_photo, validate_and_fix_image, CustomTokenRefreshView, logout_view,
)
from . import device_token_views

urlpatterns = [
    # Auth endpoints for Flutter (JWT)
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/refresh', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout', logout_view, name='auth-logout'),
    # Current user profile
    path('users/me', UsersMeView.as_view(), name='users-me'),

    # Temporary test helper
    path('users/set-test-photo', set_test_user_photo, name='set-test-photo'),
    
    # Removed Appwrite integration endpoints - using standard Django authentication
    
    # Utility endpoint (for admin/legacy purposes)
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # Simple file upload endpoints used by Flutter
    path('files/profile-picture', upload_profile_picture, name='upload-profile-picture'),
    path('files/message-attachment', upload_message_attachment, name='upload-message-attachment'),
    
    # Image validation and fixing
    path('validate-and-fix-image', validate_and_fix_image, name='validate-and-fix-image'),
    
    # Device token management for push notifications
    path('device-tokens/', device_token_views.register_device_token, name='register-device-token'),
    path('device-tokens/update/', device_token_views.update_device_token, name='update-device-token'),
    path('device-tokens/unregister/', device_token_views.unregister_device_token, name='unregister-device-token'),
    path('device-tokens/list/', device_token_views.get_device_tokens, name='get-device-tokens'),
]