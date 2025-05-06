# accounts/urls.py

from django.urls import path
from .views import (
    RegisterView, UserProfileView, UserDetailView,
    ChangePasswordView, LogoutView, update_online_status
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('update-status/', update_online_status, name='update-status'),
]