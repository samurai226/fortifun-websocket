# chat_api/asgi.py

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')

# Initialize Django before importing any models
import django
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import conversations.routing
from conversations.middleware import AppwriteAuthMiddlewareStack

# Application ASGI avec middleware JWT pour l'authentification WebSocket
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AppwriteAuthMiddlewareStack(
            URLRouter(
                conversations.routing.websocket_urlpatterns
            )
        )
    ),
})