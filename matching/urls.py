# matching/urls.py

from django.urls import path
from .views import (
    UserPreferenceView, PotentialMatchesView, MatchViewSet,
    LikeView, UnlikeView, BlockUserView, UnblockUserView,
    MatchesListView, UserInterestsView, SkipUserView
)

urlpatterns = [
    # User preferences and settings
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),
    path('interests/', UserInterestsView.as_view(), name='user-interests'),
    
    # Matching functionality
    path('potential-matches/', PotentialMatchesView.as_view(), name='potential-matches'),
    path('matches/', MatchesListView.as_view(), name='matches-list'),
    
    # User interactions
    path('like/', LikeView.as_view(), name='like-user'),
    path('unlike/', UnlikeView.as_view(), name='unlike-user'),
    path('skip/', SkipUserView.as_view(), name='skip-user'),
    path('block/', BlockUserView.as_view(), name='block-user'),
    path('unblock/', UnblockUserView.as_view(), name='unblock-user'),
    
    # Alternative endpoints for Flutter compatibility
    path('potential/', PotentialMatchesView.as_view(), name='potential-matches-alt'),
    path('matched/', MatchesListView.as_view(), name='matched-users-alt'),
]