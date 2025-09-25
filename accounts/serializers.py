# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from matching.models import UserPreference, UserInterest, UserInterestRelation
from django.conf import settings
import boto3
import os

User = get_user_model()

class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        fields = ['id', 'name']

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['min_age', 'max_age', 'max_distance', 'gender_preference']

def _build_presigned_url(key: str) -> str | None:
    if not key:
        return None
    # Already an absolute URL
    if isinstance(key, str) and key.startswith('http'):
        return key
    # Normalize to profil/<filename>
    file_name = str(key).split('/')[-1]
    s3_key = f"profil/{file_name}"
    try:
        s3 = boto3.client(
            's3',
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-west-2') or 'us-west-2',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        )
        return s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600,
        )
    except Exception:
        return None


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour la représentation générale des utilisateurs"""
    interests = serializers.SerializerMethodField()
    preferences = UserPreferenceSerializer(read_only=True)
    profile_picture = serializers.SerializerMethodField()
    
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

    def get_profile_picture(self, obj):
        # Prefer the storage key/name to build presigned URL
        key = None
        try:
            # If ImageFieldFile, .name is the key within the bucket
            key = getattr(obj.profile_picture, 'name', None) or getattr(obj, 'profile_picture', None)
        except Exception:
            key = None
        return _build_presigned_url(key)

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