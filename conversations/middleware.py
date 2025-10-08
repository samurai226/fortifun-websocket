# conversations/middleware.py

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
import jwt
from django.conf import settings

User = get_user_model()

class AppwriteAuthMiddleware(BaseMiddleware):
    """
    Simplified WebSocket authentication middleware
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Close old DB connections to avoid leaks
        close_old_connections()

        # Initialize user as anonymous
        scope['user'] = AnonymousUser()

        # Try JWT authentication first (from query parameters)
        query_string = scope.get('query_string', b'').decode('utf-8')
        if query_string:
            from urllib.parse import parse_qs
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if token:
                try:
                    # Decode JWT token
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    user_id = payload.get('user_id')
                    if user_id:
                        user = await self.get_user_from_id(user_id)
                        if user:
                            scope['user'] = user
                            return await self.inner(scope, receive, send)
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception) as e:
                    print(f"JWT authentication failed: {e}")
                    pass

        # Fallback: Try to get user from headers
        headers = dict(scope.get('headers', []))
        appwrite_user_id = headers.get(b'x-appwrite-user-id', b'').decode('utf-8')

        # For development/testing, allow anonymous connections
        if not appwrite_user_id:
            print("No authentication provided, allowing anonymous connection")
            return await self.inner(scope, receive, send)

        try:
            # Get Django user by Appwrite ID
            user = await self.get_user_from_appwrite_id(appwrite_user_id)
            if user:
                scope['user'] = user
                print(f"WebSocket authenticated user: {user.username}")
        except Exception as e:
            print(f"WebSocket authentication error: {e}")
            # Allow anonymous connection for development
            pass

        # Continue to next middleware
        return await self.inner(scope, receive, send)

    @staticmethod
    async def get_user_from_id(user_id):
        """
        Récupère l'utilisateur Django par son ID
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

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