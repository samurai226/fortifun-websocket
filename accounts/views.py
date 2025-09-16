# accounts/views.py

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from .serializers import (
    UserSerializer, UserUpdateSerializer, AppwriteUserSerializer
)
from matching.models import UserPreference

User = get_user_model()





class UserDetailView(generics.RetrieveAPIView):
    """Vue pour récupérer les détails d'un utilisateur spécifique"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)







# Nouvelles vues pour Appwrite
class AppwriteUserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour gérer les profils utilisateurs via Appwrite"""
    serializer_class = AppwriteUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        # Récupère l'utilisateur via l'ID Appwrite dans les headers
        appwrite_user_id = self.request.headers.get('X-Appwrite-User-ID')
        if appwrite_user_id:
            try:
                return User.objects.get(appwrite_user_id=appwrite_user_id)
            except User.DoesNotExist:
                # Crée un nouvel utilisateur si nécessaire
                return self._create_user_from_appwrite(appwrite_user_id)
        return self.request.user
    
    def _create_user_from_appwrite(self, appwrite_user_id):
        """Crée un utilisateur Django à partir des données Appwrite"""
        # Cette méthode sera appelée quand un utilisateur Appwrite se connecte pour la première fois
        user = User.objects.create(
            appwrite_user_id=appwrite_user_id,
            username=f"user_{appwrite_user_id[:8]}",
            is_active=True
        )
        return user

# ===================== Flutter DjangoService compatibility =====================

class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name') or ''
        first_name = name.split(' ')[0] if name else ''
        last_name = ' '.join(name.split(' ')[1:]) if name and len(name.split(' ')) > 1 else ''

        if not email or not password:
            return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        username = email.split('@')[0]
        user = User.objects.create_user(username=username, email=email, password=password,
                                        first_name=first_name, last_name=last_name)
        # create defaults
        UserPreference.objects.get_or_create(user=user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if not user:
            return Response({'detail': 'invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })


class UsersMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_picture(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'detail': 'file required'}, status=status.HTTP_400_BAD_REQUEST)
    user = request.user
    user.profile_picture = file
    user.save(update_fields=['profile_picture'])
    return Response({'detail': 'uploaded', 'url': user.profile_picture.url})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_message_attachment(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'detail': 'file required'}, status=status.HTTP_400_BAD_REQUEST)
    # In a full implementation, save to a MessageAttachment model or S3 and return URL
    # For now, reuse profile_picture storage path with a different name pattern is discouraged.
    # Return placeholder response for MVP compatibility
    return Response({'detail': 'uploaded', 'url': ''})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def appwrite_webhook(request):
    """Webhook pour recevoir les événements Appwrite"""
    try:
        event_type = request.data.get('event')
        user_data = request.data.get('data', {})
        
        if event_type == 'users.create':
            # Créer un utilisateur Django quand un utilisateur Appwrite est créé
            appwrite_user_id = user_data.get('$id')
            email = user_data.get('email')
            name = user_data.get('name', '')
            
            if appwrite_user_id and email:
                user, created = User.objects.get_or_create(
                    appwrite_user_id=appwrite_user_id,
                    defaults={
                        'email': email,
                        'username': email.split('@')[0],
                        'first_name': name.split()[0] if name else '',
                        'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                        'is_active': True
                    }
                )
                
                if created:
                    # Créer les préférences par défaut
                    UserPreference.objects.create(user=user)
        
        elif event_type == 'users.update':
            # Mettre à jour l'utilisateur Django
            appwrite_user_id = user_data.get('$id')
            if appwrite_user_id:
                try:
                    user = User.objects.get(appwrite_user_id=appwrite_user_id)
                    user.email = user_data.get('email', user.email)
                    user.first_name = user_data.get('name', '').split()[0] if user_data.get('name') else user.first_name
                    user.last_name = ' '.join(user_data.get('name', '').split()[1:]) if user_data.get('name') and len(user_data.get('name').split()) > 1 else user.last_name
                    user.save()
                except User.DoesNotExist:
                    pass
        
        elif event_type == 'users.delete':
            # Désactiver l'utilisateur Django
            appwrite_user_id = user_data.get('$id')
            if appwrite_user_id:
                try:
                    user = User.objects.get(appwrite_user_id=appwrite_user_id)
                    user.is_active = False
                    user.save()
                except User.DoesNotExist:
                    pass
        
        return Response({"detail": "Webhook traité avec succès"}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"detail": f"Erreur lors du traitement du webhook: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sync_appwrite_profile(request):
    """Synchronise le profil utilisateur avec Appwrite"""
    try:
        appwrite_user_id = request.headers.get('X-Appwrite-User-ID')
        if not appwrite_user_id:
            return Response(
                {"detail": "ID utilisateur Appwrite requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ici, vous pourriez faire un appel à l'API Appwrite pour récupérer les données
        # Pour l'instant, on retourne juste les données locales
        user = request.user
        serializer = AppwriteUserSerializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"detail": f"Erreur lors de la synchronisation: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )