# conversations/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.MainChatConsumer.as_asgi()),
    re_path(r'ws/conversations/(?P<conversation_id>\d+)/$', consumers.ConversationConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    # NEW: Anonymous chat for immediate match chat
    re_path(r'ws/anonymous-chat/(?P<room_id>[^/]+)/$', consumers.AnonymousChatConsumer.as_asgi()),
]