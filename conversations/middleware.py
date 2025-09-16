# conversations/middleware.py

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

class AppwriteAuthMiddleware(BaseMiddleware):
    """
    Middleware Appwrite personnalisé pour les WebSockets
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Fermez les anciennes connexions DB pour éviter les leaks
        close_old_connections()

        # Récupération de l'ID Appwrite depuis les headers
        headers = dict(scope.get('headers', []))
        appwrite_user_id = headers.get(b'x-appwrite-user-id', b'').decode('utf-8')

        # Initialisation de l'utilisateur comme anonyme
        scope['user'] = AnonymousUser()

        # Si aucun ID Appwrite n'est fourni, on laisse passer avec l'utilisateur anonyme
        if not appwrite_user_id:
            return await self.inner(scope, receive, send)

        try:
            # Récupération de l'utilisateur Django par l'ID Appwrite
            user = await self.get_user_from_appwrite_id(appwrite_user_id)
            if user:
                scope['user'] = user
        except Exception:
            # En cas d'erreur, l'utilisateur reste anonyme
            pass

        # Passez au suivant dans la pile de middleware
        return await self.inner(scope, receive, send)

    @staticmethod
    async def get_user_from_appwrite_id(appwrite_user_id):
        """
        Récupère l'utilisateur Django par son ID Appwrite
        """
        try:
            # Ce n'est pas vraiment asynchrone, mais devrait l'être dans un environnement de production
            # En utilisant database_sync_to_async de channels
            return User.objects.get(appwrite_user_id=appwrite_user_id)
        except User.DoesNotExist:
            return AnonymousUser()

def AppwriteAuthMiddlewareStack(inner):
    """
    Fonction utilitaire pour combiner le middleware Appwrite avec AuthMiddlewareStack
    """
    return AppwriteAuthMiddleware(AuthMiddlewareStack(inner))