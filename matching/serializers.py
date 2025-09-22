# matching/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserPreference, UserInterest, Match

User = get_user_model()

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer pour les préférences utilisateur"""
    class Meta:
        model = UserPreference
        fields = ['min_age', 'max_age', 'max_distance', 'gender_preference']
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class MatchUserSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les utilisateurs dans le contexte de matching"""
    interests = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 
                 'bio', 'location', 'is_online', 'last_activity', 'interests', 
                 'age', 'distance']
    
    def get_interests(self, obj):
        """Récupère les intérêts de l'utilisateur"""
        # Use prefetched data if available
        if hasattr(obj, '_prefetched_objects_cache') and 'interests' in obj._prefetched_objects_cache:
            return [relation.interest.name for relation in obj._prefetched_objects_cache['interests']]
        
        # Fallback to direct query
        from matching.models import UserInterestRelation
        interest_relations = UserInterestRelation.objects.filter(user=obj).select_related('interest')
        return [relation.interest.name for relation in interest_relations]
    
    def get_age(self, obj):
        """Calcule l'âge de l'utilisateur à partir de sa date de naissance"""
        from datetime import date
        if not obj.date_of_birth:
            return None
        
        today = date.today()
        born = obj.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    
    def get_distance(self, obj):
        """Calcule la distance entre l'utilisateur courant et cet utilisateur"""
        request = self.context.get('request')
        if not request or not obj.latitude or not obj.longitude:
            return None
        
        # Get current user from Django authentication
        current_user = request.user if request.user.is_authenticated else None
        if not current_user or not current_user.latitude or not current_user.longitude:
            return None
        
        # Calcul de la distance en km en utilisant la formule de Haversine
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lon1, lat1, lon2, lat2):
            # Convert decimal degrees to radians
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            
            # Haversine formula
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of Earth in kilometers
            return c * r
        
        distance = haversine(
            current_user.longitude, current_user.latitude,
            obj.longitude, obj.latitude
        )
        
        return round(distance, 1)

class MatchSerializer(serializers.ModelSerializer):
    """Serializer pour les matchs"""
    matched_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = ['id', 'created_at', 'is_active', 'matched_user']
        read_only_fields = ['id', 'created_at', 'matched_user']
    
    def get_matched_user(self, obj):
        """Récupère l'utilisateur correspondant au match"""
        request = self.context.get('request')
        if not request:
            return None
        
        # Get current user from Django authentication
        current_user = request.user if request.user.is_authenticated else None
        if not current_user:
            return None
        
        try:
            # Récupère l'autre utilisateur du match
            if obj.user1 == current_user:
                matched_user = obj.user2
            else:
                matched_user = obj.user1
            
            return MatchUserSerializer(matched_user, context=self.context).data
        except User.DoesNotExist:
            return None

class LikeUserSerializer(serializers.Serializer):
    """Serializer pour l'action de liker un utilisateur"""
    user_id = serializers.IntegerField(required=True)
    
    def validate_user_id(self, value):
        """Vérifie que l'utilisateur existe"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("L'utilisateur spécifié n'existe pas.")
        
        # Vérifie que l'utilisateur n'essaie pas de se liker lui-même
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            current_user = request.user
            if current_user.id == value:
                raise serializers.ValidationError("Vous ne pouvez pas vous liker vous-même.")
        
        return value