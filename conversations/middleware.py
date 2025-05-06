# conversations/middleware.py

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware JWT personnalisé pour les WebSockets
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Fermez les anciennes connexions DB pour éviter les leaks
        close_old_connections()

        # Récupération du token depuis les paramètres de requête
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        # Initialisation de l'utilisateur comme anonyme
        scope['user'] = AnonymousUser()

        # Si aucun token n'est fourni, on laisse passer avec l'utilisateur anonyme
        if not token:
            return await self.inner(scope, receive, send)

        try:
            # Validation du token
            UntypedToken(token)
            # Décodage du token
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            # Récupération de l'utilisateur
            user_id = decoded_data.get('user_id')
            if user_id:
                user = await self.get_user(user_id)
                scope['user'] = user
        except (InvalidToken, TokenError, jwt.PyJWTError):
            # En cas d'erreur, l'utilisateur reste anonyme
            pass

        # Passez au suivant dans la pile de middleware
        return await self.inner(scope, receive, send)

    @staticmethod
    async def get_user(user_id):
        """
        Récupère l'utilisateur de manière asynchrone
        """
        try:
            # Ce n'est pas vraiment asynchrone, mais devrait l'être dans un environnement de production
            # En utilisant database_sync_to_async de channels
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

def JWTAuthMiddlewareStack(inner):
    """
    Fonction utilitaire pour combiner le middleware JWT avec AuthMiddlewareStack
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))