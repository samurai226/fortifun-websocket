# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DeviceToken

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user data"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email'
        ]

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = [
            'id',
            'device_token',
            'device_type',
            'app_version',
            'is_active',
            'created_at',
            'updated_at',
            'last_used'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']