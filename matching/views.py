# matching/views.py

from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, F, Prefetch
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import timedelta, date
from .models import UserPreference, UserInterest, Match
from .serializers import (
    UserPreferenceSerializer, MatchUserSerializer,
    MatchSerializer, LikeUserSerializer
)
from conversations.notifications import notify_new_match, notify_like

User = get_user_model()

def get_current_user(request):
    """Helper function to get current user from Django authentication"""
    return request.user if request.user.is_authenticated else None

class CustomPagination(PageNumberPagination):
    """Pagination personnalisée pour les listes"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class MatchingRateThrottle(UserRateThrottle):
    """Rate limiting spécifique pour les actions de matching"""
    rate = '100/hour'  # 100 actions par heure par utilisateur

class LikeRateThrottle(UserRateThrottle):
    """Rate limiting pour les likes"""
    rate = '50/hour'  # 50 likes par heure par utilisateur

class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """Vue pour récupérer et mettre à jour les préférences de l'utilisateur"""
    serializer_class = UserPreferenceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [MatchingRateThrottle]
    
    def get_object(self):
        current_user = get_current_user(self.request)
        if not current_user:
            return None
        
        # Récupère ou crée les préférences de l'utilisateur
        obj, created = UserPreference.objects.get_or_create(user=current_user)
        return obj

class UserInterestsView(generics.ListCreateAPIView):
    """Vue pour gérer les intérêts de l'utilisateur"""
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [MatchingRateThrottle]
    
    def get_queryset(self):
        """Récupère tous les intérêts disponibles"""
        return UserInterest.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserPreferenceSerializer
        return UserPreferenceSerializer
    
    def list(self, request, *args, **kwargs):
        """Liste tous les intérêts avec indication de ceux de l'utilisateur"""
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        all_interests = self.get_queryset()
        user_interests = current_user.interests.all()
        
        interests_data = []
        for interest in all_interests:
            interests_data.append({
                'id': interest.id,
                'name': interest.name,
                'is_selected': interest in user_interests
            })
        
        return Response(interests_data)
    
    def create(self, request, *args, **kwargs):
        """Met à jour les intérêts de l'utilisateur"""
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        interest_ids = request.data.get('interest_ids', [])
        
        # Supprime tous les intérêts actuels
        current_user.interests.all().delete()
        
        # Ajoute les nouveaux intérêts
        for interest_id in interest_ids:
            try:
                interest = UserInterest.objects.get(id=interest_id)
                current_user.interests.create(interest=interest)
            except UserInterest.DoesNotExist:
                continue
        
        # Invalide le cache des matches potentiels
        cache_key = f"potential_matches_{current_user.id}"
        cache.delete(cache_key)
        
        return Response({
            'detail': 'Intérêts mis à jour avec succès'
        }, status=status.HTTP_200_OK)

class PotentialMatchesView(generics.ListAPIView):
    """Vue pour lister les utilisateurs potentiels pour le matching"""
    serializer_class = MatchUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'bio', 'location']
    ordering_fields = ['last_activity', 'is_online', 'date_joined']
    ordering = ['-is_online', '-last_activity']
    throttle_classes = [MatchingRateThrottle]
    
    def get_queryset(self):
        current_user = get_current_user(self.request)
        if not current_user:
            return User.objects.none()
        
        user = current_user
        
        # Vérifie le cache d'abord
        cache_key = f"potential_matches_{user.id}"
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
        
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
        ).select_related().prefetch_related(
            Prefetch('interests', queryset=UserInterest.objects.all())
        )
        
        # Filtres avancés
        queryset = self._apply_advanced_filters(queryset, preferences)
        
        # Applique les filtres de recherche personnalisés
        queryset = self._apply_custom_filters(queryset)
        
        # Cache le résultat pour 5 minutes
        cache.set(cache_key, queryset, 300)
        
        return queryset
    
    def _apply_advanced_filters(self, queryset, preferences):
        """Applique les filtres avancés basés sur les préférences"""
        
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
            if hasattr(User, 'gender'):
                queryset = queryset.filter(gender=preferences.gender_preference)
        
        # Filtre par distance si les coordonnées sont disponibles
        current_user = get_current_user(self.request)
        if preferences.max_distance and current_user and current_user.latitude and current_user.longitude:
            # Note: Pour une implémentation complète, utilisez PostGIS ou une solution géospatiale
            pass
        
        # Filtre par activité récente (utilisateurs actifs dans les 7 derniers jours)
        active_threshold = timezone.now() - timedelta(days=7)
        queryset = queryset.filter(
            Q(last_activity__gte=active_threshold) | Q(is_online=True)
        )
        
        return queryset
    
    def _apply_custom_filters(self, queryset):
        """Applique les filtres personnalisés depuis les paramètres de requête"""
        
        # Filtre par intérêts communs
        common_interests = self.request.query_params.get('common_interests')
        if common_interests:
            interest_ids = [int(x) for x in common_interests.split(',') if x.isdigit()]
            if interest_ids:
                queryset = queryset.filter(interests__interest_id__in=interest_ids).distinct()
        
        # Filtre par statut en ligne
        online_only = self.request.query_params.get('online_only')
        if online_only == 'true':
            queryset = queryset.filter(is_online=True)
        
        # Filtre par distance maximale
        max_distance = self.request.query_params.get('max_distance')
        if max_distance and max_distance.isdigit():
            # Implémentation de filtre par distance
            pass
        
        return queryset

class MatchesListView(generics.ListAPIView):
    """Vue pour lister les matchs de l'utilisateur"""
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = CustomPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'is_active']
    ordering = ['-created_at']
    throttle_classes = [MatchingRateThrottle]
    
    def get_queryset(self):
        current_user = get_current_user(self.request)
        if not current_user:
            return Match.objects.none()
        
        user = current_user
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            is_active=True
        ).select_related('user1', 'user2').order_by('-created_at')

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les matchs"""
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = CustomPagination
    throttle_classes = [MatchingRateThrottle]
    
    def get_queryset(self):
        current_user = get_current_user(self.request)
        if not current_user:
            return Match.objects.none()
        
        user = current_user
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            is_active=True
        )

class LikeView(generics.CreateAPIView):
    """Vue pour liker un utilisateur"""
    serializer_class = LikeUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [LikeRateThrottle]
    
    def create(self, request, *args, **kwargs):
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = current_user
        liked_user_id = serializer.validated_data['user_id']
        liked_user = User.objects.get(id=liked_user_id)
        
        # Vérifie si l'utilisateur n'est pas déjà liké
        if user.liked_users.filter(id=liked_user_id).exists():
            return Response({
                'detail': 'Utilisateur déjà liké'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifie si l'utilisateur n'est pas bloqué
        if user.blocked_users.filter(id=liked_user_id).exists():
            return Response({
                'detail': 'Impossible de liker un utilisateur bloqué'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
            
            # Invalide le cache des matches
            cache.delete(f"potential_matches_{user.id}")
            cache.delete(f"potential_matches_{liked_user.id}")
            
            return Response({
                'detail': 'Like enregistré avec succès',
                'is_match': True,
                'match': MatchSerializer(match, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'detail': 'Like enregistré avec succès',
            'is_match': False
        }, status=status.HTTP_201_CREATED)

class SkipUserView(generics.CreateAPIView):
    """Vue pour passer un utilisateur (équivalent à unlike mais sans notification)"""
    serializer_class = LikeUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [LikeRateThrottle]
    
    def create(self, request, *args, **kwargs):
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = current_user
        skipped_user_id = serializer.validated_data['user_id']
        skipped_user = User.objects.get(id=skipped_user_id)
        
        # Supprime l'utilisateur des likes s'il était liké
        user.liked_users.remove(skipped_user)
        
        # Désactive le match s'il existait
        if user.id < skipped_user.id:
            user1, user2 = user, skipped_user
        else:
            user1, user2 = skipped_user, user
        
        try:
            match = Match.objects.get(user1=user1, user2=user2)
            match.is_active = False
            match.save()
        except Match.DoesNotExist:
            pass
        
        # Invalide le cache
        cache.delete(f"potential_matches_{user.id}")
        
        return Response({
            'detail': 'Utilisateur passé avec succès'
        }, status=status.HTTP_200_OK)

class UnlikeView(generics.CreateAPIView):
    """Vue pour annuler un like"""
    serializer_class = LikeUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [LikeRateThrottle]
    
    def create(self, request, *args, **kwargs):
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = current_user
        unliked_user_id = serializer.validated_data['user_id']
        unliked_user = User.objects.get(id=unliked_user_id)
        
        # Vérifie si l'utilisateur était liké
        if not user.liked_users.filter(id=unliked_user_id).exists():
            return Response({
                'detail': 'Utilisateur non liké'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # Invalide le cache
        cache.delete(f"potential_matches_{user.id}")
        cache.delete(f"potential_matches_{unliked_user.id}")
        
        return Response({
            'detail': 'Like annulé avec succès'
        }, status=status.HTTP_200_OK)

class BlockUserView(generics.CreateAPIView):
    """Vue pour bloquer un utilisateur"""
    serializer_class = LikeUserSerializer  # Réutilisation du même serializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [MatchingRateThrottle]
    
    def create(self, request, *args, **kwargs):
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = current_user
        blocked_user_id = serializer.validated_data['user_id']
        blocked_user = User.objects.get(id=blocked_user_id)
        
        # Vérifie si l'utilisateur n'est pas déjà bloqué
        if user.blocked_users.filter(id=blocked_user_id).exists():
            return Response({
                'detail': 'Utilisateur déjà bloqué'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # Invalide le cache
        cache.delete(f"potential_matches_{user.id}")
        cache.delete(f"potential_matches_{blocked_user.id}")
        
        return Response({
            'detail': 'Utilisateur bloqué avec succès'
        }, status=status.HTTP_200_OK)

class UnblockUserView(generics.CreateAPIView):
    """Vue pour débloquer un utilisateur"""
    serializer_class = LikeUserSerializer  # Réutilisation du même serializer
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [MatchingRateThrottle]
    
    def create(self, request, *args, **kwargs):
        current_user = get_current_user(request)
        if not current_user:
            return Response(
                {"detail": "Utilisateur Appwrite non trouvé"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = current_user
        unblocked_user_id = serializer.validated_data['user_id']
        unblocked_user = User.objects.get(id=unblocked_user_id)
        
        # Vérifie si l'utilisateur était bloqué
        if not user.blocked_users.filter(id=unblocked_user_id).exists():
            return Response({
                'detail': 'Utilisateur non bloqué'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supprime l'utilisateur de la liste des bloqués
        user.blocked_users.remove(unblocked_user)
        
        # Invalide le cache
        cache.delete(f"potential_matches_{user.id}")
        cache.delete(f"potential_matches_{unblocked_user.id}")
        
        return Response({
            'detail': 'Utilisateur débloqué avec succès'
        }, status=status.HTTP_200_OK)