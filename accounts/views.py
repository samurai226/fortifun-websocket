# accounts/views.py

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .serializers import (
    UserSerializer, UserRegisterSerializer, UserUpdateSerializer,
    ChangePasswordSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """Vue pour l'inscription des utilisateurs"""
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour récupérer et mettre à jour le profil de l'utilisateur connecté"""
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserSerializer
    
    def retrieve(self, request, *args, **kwargs):
        # Met à jour le statut en ligne de l'utilisateur
        request.user.is_online = True
        request.user.last_activity = timezone.now()
        request.user.save(update_fields=['is_online', 'last_activity'])
        
        return super().retrieve(request, *args, **kwargs)

class UserDetailView(generics.RetrieveAPIView):
    """Vue pour récupérer les détails d'un utilisateur spécifique"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ChangePasswordView(generics.UpdateAPIView):
    """Vue pour changer le mot de passe"""
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifie l'ancien mot de passe
        user = self.get_object()
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": ["Le mot de passe actuel est incorrect."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Change le mot de passe
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {"detail": "Mot de passe changé avec succès"},
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    """Vue pour la déconnexion (invalidation du token)"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        try:
            # Met à jour le statut de l'utilisateur
            request.user.is_online = False
            request.user.save(update_fields=['is_online'])
            
            # Récupère et blackliste le token de rafraîchissement
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response(
                {"detail": "Déconnexion réussie"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_online_status(request):
    """Vue pour mettre à jour le statut en ligne de l'utilisateur"""
    user = request.user
    user.last_activity = timezone.now()
    user.is_online = True
    user.save(update_fields=['is_online', 'last_activity'])
    
    return Response(
        {"detail": "Statut en ligne mis à jour"},
        status=status.HTTP_200_OK
    )