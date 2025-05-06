# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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
                 'last_activity', 'interests', 'preferences']
        read_only_fields = ['id', 'is_online', 'last_activity']
    
    def get_interests(self, obj):
        interest_relations = UserInterestRelation.objects.filter(user=obj)
        interests = [relation.interest for relation in interest_relations]
        return UserInterestSerializer(interests, many=True).data

class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription des utilisateurs"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Création automatique des préférences par défaut
        UserPreference.objects.create(user=user)
        
        return user

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

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Les nouveaux mots de passe ne correspondent pas."})
        return attrs