# conversations/views.py

from rest_framework import status, generics, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import Conversation, Message, MessageRead
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    MessageSerializer, MessageCreateSerializer
)
from .notifications import notify_new_message  # Ajout de l'import pour les notifications

class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les conversations"""
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user,
            is_active=True
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        
        # Notifier l'autre utilisateur qu'une nouvelle conversation a été créée
        # Ce code suppose que la méthode save du serializer retourne la conversation
        for participant in conversation.participants.all():
            if participant != request.user:
                message = conversation.messages.last()
                if message:
                    # Prépare les données du message pour la notification
                    message_data = {
                        'id': message.id,
                        'conversation_id': conversation.id,
                        'sender': {
                            'id': request.user.id,
                            'username': request.user.username,
                            'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None
                        },
                        'content': message.content,
                        'created_at': message.created_at.isoformat()
                    }
                    
                    # Envoie la notification
                    notify_new_message(participant.id, message_data)
        
        # Retourne la conversation créée avec le serializer standard
        result_serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """Permet à un utilisateur de quitter/supprimer une conversation"""
        conversation = self.get_object()
        
        # Pour simplifier, nous marquons simplement la conversation comme inactive
        # Une approche alternative serait de supprimer l'utilisateur des participants
        conversation.is_active = False
        conversation.save()
        
        return Response(
            {"detail": "Conversation supprimée avec succès"},
            status=status.HTTP_200_OK
        )

class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet pour les messages"""
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_pk')
        
        # Vérifie que l'utilisateur fait partie de la conversation
        user = self.request.user
        conversation = Conversation.objects.filter(
            id=conversation_id,
            participants=user
        ).first()
        
        if not conversation:
            return Message.objects.none()
        
        return Message.objects.filter(conversation=conversation)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(sender=request.user)
        
        # Récupérer la conversation
        conversation_id = self.kwargs.get('conversation_pk')
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Mettre à jour la date de dernière modification de la conversation
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        
        # Notifier les autres participants
        for participant in conversation.participants.all():
            if participant != request.user:
                # Prépare les données du message pour la notification
                message_data = {
                    'id': message.id,
                    'conversation_id': conversation.id,
                    'sender': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'profile_picture': request.user.profile_picture.url if request.user.profile_picture else None
                    },
                    'content': message.content,
                    'created_at': message.created_at.isoformat()
                }
                
                # Envoie la notification
                notify_new_message(participant.id, message_data)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Marque tous les messages comme lus par l'utilisateur courant
        if response.status_code == status.HTTP_200_OK:
            conversation_id = self.kwargs.get('conversation_pk')
            user = request.user
            
            # Récupère tous les messages qui ne sont pas de l'utilisateur courant et qui n'ont pas encore été lus
            messages = Message.objects.filter(
                conversation_id=conversation_id
            ).exclude(
                sender=user
            ).exclude(
                read_receipts__user=user
            )
            
            # Crée des enregistrements de lecture pour ces messages
            for message in messages:
                MessageRead.objects.get_or_create(message=message, user=user)
            
        return response
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None, conversation_pk=None):
        """Marque un message spécifique comme lu"""
        message = self.get_object()
        
        # Crée un enregistrement de lecture si nécessaire
        MessageRead.objects.get_or_create(message=message, user=request.user)
        
        return Response(
            {"detail": "Message marqué comme lu"},
            status=status.HTTP_200_OK
        )