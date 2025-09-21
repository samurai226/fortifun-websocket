# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from matching.models import UserPreference, UserInterest, UserInterestRelation

User = get_user_model()

class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        fields = ['id', 'name']

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['min_age', 'max_age', 'max_distance', 'gender_preference']

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour la représentation générale des utilisateurs"""
    interests = serializers.SerializerMethodField()
    preferences = UserPreferenceSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile_picture', 
                 'bio', 'date_of_birth', 'phone_number', 'location', 'is_online', 
                 'last_activity', 'interests', 'preferences', 'appwrite_user_id']
        read_only_fields = ['id', 'is_online', 'last_activity', 'appwrite_user_id']
    
    def get_interests(self, obj):
        interest_relations = UserInterestRelation.objects.filter(user=obj)
        interests = [relation.interest for relation in interest_relations]
        return UserInterestSerializer(interests, many=True).data

# Removed AppwriteUserSerializer - using standard UserSerializer



class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil utilisateur"""
    interests = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture', 
                 'bio', 'date_of_birth', 'phone_number', 'location', 'latitude', 'longitude', 
                 'interests']
    
    def update(self, instance, validated_data):
        interests_data = validated_data.pop('interests', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les intérêts si fournis
        if interests_data is not None:
            # Supprimer les relations existantes
            UserInterestRelation.objects.filter(user=instance).delete()
            
            # Ajouter les nouvelles relations
            for interest_name in interests_data:
                interest, created = UserInterest.objects.get_or_create(name=interest_name.lower())
                UserInterestRelation.objects.create(user=instance, interest=interest)
        
        return instance



# Removed AppwriteWebhookSerializer - using standard Django authentication