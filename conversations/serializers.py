# conversations/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message, MessageRead

User = get_user_model()

class MessageUserSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les utilisateurs dans les messages"""
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']

class MessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages"""
    sender = MessageUserSerializer(read_only=True)
    is_read_by_recipient = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'created_at', 
                 'is_read', 'attachment', 'is_read_by_recipient']
        read_only_fields = ['id', 'created_at', 'is_read', 'is_read_by_recipient']
    
    def get_is_read_by_recipient(self, obj):
        """Vérifie si le message a été lu par le destinataire"""
        request = self.context.get('request')
        if not request or request.user == obj.sender:
            # Si l'utilisateur est l'expéditeur, on vérifie si le message a été lu par quelqu'un d'autre
            return MessageRead.objects.filter(message=obj).exclude(user=obj.sender).exists()
        else:
            # Si l'utilisateur est un destinataire, on vérifie s'il a lu le message
            return MessageRead.objects.filter(message=obj, user=request.user).exists()

class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de messages"""
    class Meta:
        model = Message
        fields = ['conversation', 'content', 'attachment']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        # Get user from JWT authentication
        user = request.user
        if not user or user.is_anonymous:
            raise serializers.ValidationError("User must be authenticated")
        
        validated_data['sender'] = user
        return super().create(validated_data)

class ConversationSerializer(serializers.ModelSerializer):
    """Serializer pour les conversations"""
    participants = MessageUserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 
                 'is_active', 'last_message', 'unread_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_message', 'unread_count']
    
    def get_last_message(self, obj):
        """Récupère le dernier message de la conversation"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        """Compte les messages non lus par l'utilisateur courant"""
        request = self.context.get('request')
        if not request or not request.user or request.user.is_anonymous:
            return 0
        
        try:
            user = request.user
            
            # Compter les messages qui n'ont pas été lus par l'utilisateur courant
            messages = obj.messages.all()
            read_message_ids = MessageRead.objects.filter(
                message__in=messages, 
                user=user
            ).values_list('message_id', flat=True)
            
            # Ne pas compter les messages envoyés par l'utilisateur lui-même
            unread_count = messages.exclude(
                id__in=read_message_ids
            ).exclude(
                sender=user
            ).count()
            
            return unread_count
        except Exception:
            return 0

class ConversationCreateSerializer(serializers.Serializer):
    """Serializer pour créer une nouvelle conversation"""
    participant_id = serializers.IntegerField(required=True)
    message = serializers.CharField(required=True)
    
    def validate_participant_id(self, value):
        """Vérifie que l'utilisateur existe"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("L'utilisateur spécifié n'existe pas.")
        
        # Vérifie que l'utilisateur n'essaie pas de créer une conversation avec lui-même
        request = self.context.get('request')
        if request and request.user.id == value:
            raise serializers.ValidationError("Vous ne pouvez pas créer une conversation avec vous-même.")
        
        return value
    
    def create(self, validated_data):
        participant_id = validated_data['participant_id']
        message_content = validated_data['message']
        request = self.context.get('request')
        
        if not request or not request.user or request.user.is_anonymous:
            raise serializers.ValidationError("User must be authenticated")
        
        try:
            user1 = request.user
            user2 = User.objects.get(id=participant_id)
            
            # Vérifie si une conversation existe déjà entre ces utilisateurs
            conversations = Conversation.objects.filter(participants=user1).filter(participants=user2)
            
            if conversations.exists():
                conversation = conversations.first()
            else:
                # Création d'une nouvelle conversation
                conversation = Conversation.objects.create()
                conversation.participants.add(user1, user2)
            
            # Création du premier message
            Message.objects.create(
                conversation=conversation,
                sender=user1,
                content=message_content
            )
            
            return conversation
        except User.DoesNotExist:
            raise serializers.ValidationError("Participant user not found")
