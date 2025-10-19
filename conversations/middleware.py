# conversations/middleware.py

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
import jwt
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT-based WebSocket authentication middleware
    Supports both query parameter and header-based JWT tokens
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Close old DB connections to avoid leaks
        close_old_connections()

        # Initialize user as anonymous
        scope['user'] = AnonymousUser()

        # Try JWT authentication from query parameters first
        query_string = scope.get('query_string', b'').decode('utf-8')
        token = None
        
        if query_string:
            from urllib.parse import parse_qs
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

        # Try JWT authentication from headers if not in query params
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode('utf-8')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Authenticate with JWT token if available
        if token:
            try:
                user = await self.authenticate_jwt_token(token)
                if user and not user.is_anonymous:
                    scope['user'] = user
                    print(f"WebSocket authenticated user: {user.username} (ID: {user.id})")
                    return await self.inner(scope, receive, send)
                else:
                    print("JWT token valid but user not found")
            except Exception as e:
                print(f"JWT authentication failed: {e}")
                # Continue to allow anonymous connection for development

        # For development/testing, allow anonymous connections
        print("No valid JWT token provided, allowing anonymous connection for development")
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def authenticate_jwt_token(self, token):
        """
        Authenticate user using JWT token
        """
        try:
            # Try using SimpleJWT first (preferred)
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            if user_id:
                return User.objects.get(id=user_id)
        except (TokenError, InvalidToken, User.DoesNotExist):
            pass

        try:
            # Fallback to manual JWT decoding
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if user_id:
                return User.objects.get(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            pass

        return AnonymousUser()

def JWTAuthMiddlewareStack(inner):
    """
    Utility function to combine JWT middleware with AuthMiddlewareStack
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))