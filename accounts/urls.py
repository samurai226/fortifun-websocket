# accounts/urls.py

from django.urls import path
from .views import (
    UserDetailView,
    RegisterView, LoginView, UsersMeView, upload_profile_picture, upload_message_attachment,
    set_test_user_photo, reprocess_all_images,
)

urlpatterns = [
    # Auth endpoints for Flutter (JWT)
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login', LoginView.as_view(), name='auth-login'),
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
    
    # Image reprocessing endpoint (temporary)
    path('admin/reprocess-images', reprocess_all_images, name='reprocess-images'),
]