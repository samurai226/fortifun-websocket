# matching/urls.py

from django.urls import path
from .views import (
    UserPreferenceView, PotentialMatchesView,
    LikeView, UnlikeView, BlockUserView, UnblockUserView
)

urlpatterns = [
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),
    path('potential-matches/', PotentialMatchesView.as_view(), name='potential-matches'),
    path('like/', LikeView.as_view(), name='like-user'),
    path('unlike/', UnlikeView.as_view(), name='unlike-user'),
    path('block/', BlockUserView.as_view(), name='block-user'),
    path('unblock/', UnblockUserView.as_view(), name='unblock-user'),
]