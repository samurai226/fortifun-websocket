# matching/views.py

from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta, date
from .models import UserPreference, UserInterest, Match
from .serializers import (
    UserPreferenceSerializer, MatchUserSerializer,
    MatchSerializer, LikeUserSerializer
)
from conversations.notifications import notify_new_match, notify_like  # Ajout de l'import pour les notifications

User = get_user_model()

class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """Vue pour récupérer et mettre à jour les préférences de l'utilisateur"""
    serializer_class = UserPreferenceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        # Récupère ou crée les préférences de l'utilisateur
        obj, created = UserPreference.objects.get_or_create(user=self.request.user)
        return obj

class PotentialMatchesView(generics.ListAPIView):
    """Vue pour lister les utilisateurs potentiels pour le matching"""
    serializer_class = MatchUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        
        # Récupère les préférences de l'utilisateur
        try:
            preferences = UserPreference.objects.get(user=user)
        except UserPreference.DoesNotExist:
            preferences = UserPreference.objects.create(user=user)
        
        # Utilisateurs déjà likés ou bloqués
        liked_users = user.liked_users.all()
        blocked_users = user.blocked_users.all()
        
        # Filtre de base : exclure l'utilisateur courant, les utilisateurs likés et bloqués
        queryset = User.objects.exclude(
            Q(id=user.id) | Q(id__in=liked_users) | Q(id__in=blocked_users)
        )
        
        # Filtre par âge si la date de naissance est disponible
        if preferences.min_age or preferences.max_age:
            today = date.today()
            
            if preferences.min_age:
                max_birthdate = today - timedelta(days=preferences.min_age * 365)
                queryset = queryset.filter(Q(date_of_birth__isnull=False) & Q(date_of_birth__lte=max_birthdate))
            
            if preferences.max_age:
                min_birthdate = today - timedelta(days=preferences.max_age * 365)
                queryset = queryset.filter(Q(date_of_birth__isnull=False) & Q(date_of_birth__gte=min_birthdate))
        
        # Filtre par genre si spécifié
        if preferences.gender_preference and preferences.gender_preference != 'A':
            # Remarque : ce filtre assume que le modèle User a un champ 'gender'
            # Si ce n'est pas le cas, vous devrez l'adapter ou le supprimer
            if hasattr(User, 'gender'):
                queryset = queryset.filter(gender=preferences.gender_preference)
        
        # Trier par activité récente et similarité d'intérêts
        queryset = queryset.order_by('-is_online', '-last_activity')
        
        return queryset

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les matchs"""
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            is_active=True
        )

class LikeView(generics.CreateAPIView):
    """Vue pour liker un utilisateur"""
    serializer_class = LikeUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        liked_user_id = serializer.validated_data['user_id']
        liked_user = User.objects.get(id=liked_user_id)
        
        # Ajoute l'utilisateur liké
        user.liked_users.add(liked_user)
        
        # Prépare les données du like pour la notification
        liker_data = {
            'id': user.id,
            'username': user.username,
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        }
        
        # Notifie l'utilisateur liké (si la fonctionnalité est activée dans les préférences)
        notify_like(liked_user.id, liker_data)
        
        # Vérifie s'il y a un match (like mutuel)
        is_match = liked_user.liked_users.filter(id=user.id).exists()
        
        if is_match:
            # Crée un match dans la base de données
            # Nous ordonnons les utilisateurs par ID pour éviter les doublons
            if user.id < liked_user.id:
                user1, user2 = user, liked_user
            else:
                user1, user2 = liked_user, user
            
            match, created = Match.objects.get_or_create(
                user1=user1, 
                user2=user2,
                defaults={'is_active': True}
            )
            
            if not created and not match.is_active:
                match.is_active = True
                match.save()
            
            # Prépare les données du match pour la notification
            match_data = {
                'id': match.id,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'profile_picture': user.profile_picture.url if user.profile_picture else None
                },
                'created_at': match.created_at.isoformat() if created else timezone.now().isoformat()
            }
            
            # Notifie l'autre utilisateur du match
            notify_new_match(liked_user.id, match_data)
            
            # Modifie les données du match pour la réponse à l'utilisateur actuel
            match_data['user'] = {
                'id': liked_user.id,
                'username': liked_user.username,
                'profile_picture': liked_user.profile_picture.url if liked_user.profile_picture else None
            }
            
            return Response({
                'detail': 'Like enregistré avec succès',
                'is_match': True,
                'match': MatchSerializer(match, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'detail': 'Like enregistré avec succès',
            'is_match': False
        }, status=status.HTTP_201_CREATED)

class UnlikeView(generics.CreateAPIView):
    """Vue pour annuler un like"""
    serializer_class = LikeUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        unliked_user_id = serializer.validated_data['user_id']
        unliked_user = User.objects.get(id=unliked_user_id)
        
        # Supprime l'utilisateur des likes
        user.liked_users.remove(unliked_user)
        
        # Désactive le match s'il existait
        if user.id < unliked_user.id:
            user1, user2 = user, unliked_user
        else:
            user1, user2 = unliked_user, user
        
        try:
            match = Match.objects.get(user1=user1, user2=user2)
            match.is_active = False
            match.save()
        except Match.DoesNotExist:
            pass
        
        return Response({
            'detail': 'Like annulé avec succès'
        }, status=status.HTTP_200_OK)

class BlockUserView(generics.CreateAPIView):
    """Vue pour bloquer un utilisateur"""
    serializer_class = LikeUserSerializer  # Réutilisation du même serializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        # Reste du code inchangé...
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        blocked_user_id = serializer.validated_data['user_id']
        blocked_user = User.objects.get(id=blocked_user_id)
        
        # Ajoute l'utilisateur à la liste des bloqués
        user.blocked_users.add(blocked_user)
        
        # Supprime des likes mutuels si existants
        user.liked_users.remove(blocked_user)
        user.liked_by.remove(blocked_user)
        
        # Désactive le match s'il existait
        if user.id < blocked_user.id:
            user1, user2 = user, blocked_user
        else:
            user1, user2 = blocked_user, user
        
        try:
            match = Match.objects.get(user1=user1, user2=user2)
            match.is_active = False
            match.save()
        except Match.DoesNotExist:
            pass
        
        return Response({
            'detail': 'Utilisateur bloqué avec succès'
        }, status=status.HTTP_200_OK)

class UnblockUserView(generics.CreateAPIView):
    """Vue pour débloquer un utilisateur"""
    serializer_class = LikeUserSerializer  # Réutilisation du même serializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        # Reste du code inchangé...
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        unblocked_user_id = serializer.validated_data['user_id']
        unblocked_user = User.objects.get(id=unblocked_user_id)
        
        # Supprime l'utilisateur de la liste des bloqués
        user.blocked_users.remove(unblocked_user)
        
        return Response({
            'detail': 'Utilisateur débloqué avec succès'
        }, status=status.HTTP_200_OK)