# conversations/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conversation, Message, MessageRead

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consommateur pour les conversations en temps réel
    """
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            # Rejeter la connexion si l'utilisateur n'est pas authentifié
            await self.close()
            return
        
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Vérifier si l'utilisateur est bien un participant de cette conversation
        is_participant = await self.is_conversation_participant(self.conversation_id, self.user.id)
        if not is_participant:
            await self.close()
            return
        
        # Rejoindre le groupe de la conversation
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Mettre à jour le statut en ligne de l'utilisateur
        await self.update_user_status(self.user.id, True)
        
        # Notifier les autres participants que l'utilisateur est en ligne
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online',
                'timestamp': timezone.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        # Quitter le groupe de la conversation
        if hasattr(self, 'room_group_name'):
            # Notifier les autres participants que l'utilisateur est hors ligne
            if hasattr(self, 'user') and not self.user.is_anonymous:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_status',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'status': 'offline',
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
                # Mettre à jour le statut de l'utilisateur
                await self.update_user_status(self.user.id, False)
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')
        
        if message_type == 'message':
            # Traiter un nouveau message
            content = text_data_json.get('content')
            attachment_url = text_data_json.get('attachment')
            
            if content:
                # Sauvegarder le message dans la base de données
                message = await self.save_message(
                    self.conversation_id,
                    self.user.id,
                    content,
                    attachment_url
                )
                
                # Envoyer le message à tous les membres du groupe
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'sender_id': self.user.id,
                            'sender_username': self.user.username,
                            'sender_profile_picture': self.user.profile_picture.url if self.user.profile_picture else None,
                            'content': content,
                            'created_at': message.created_at.isoformat(),
                            'is_read': False,
                            'attachment': message.attachment.url if message.attachment else None,
                        }
                    }
                )
        
        elif message_type == 'read_receipt':
            # Traiter un accusé de lecture
            message_id = text_data_json.get('message_id')
            
            if message_id:
                # Marquer le message comme lu
                await self.mark_message_read(message_id, self.user.id)
                
                # Notifier tous les membres du groupe
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipt',
                        'message_id': message_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'timestamp': timezone.now().isoformat()
                    }
                )
        
        elif message_type == 'typing':
            # Notifier que l'utilisateur est en train d'écrire
            is_typing = text_data_json.get('is_typing', True)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing
                }
            )

    async def chat_message(self, event):
        """Envoyer un message au client WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def read_receipt(self, event):
        """Envoyer un accusé de lecture au client WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def user_typing(self, event):
        """Envoyer une notification de frappe au client WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def user_status(self, event):
        """Envoyer une notification de changement de statut au client WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def is_conversation_participant(self, conversation_id, user_id):
        """Vérifie si l'utilisateur est un participant de la conversation"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.filter(id=user_id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, conversation_id, user_id, content, attachment_url=None):
        """Sauvegarde un message dans la base de données"""
        conversation = Conversation.objects.get(id=conversation_id)
        user = User.objects.get(id=user_id)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        
        # Si une pièce jointe existe, il faudrait la traiter ici
        # Note: le traitement complet des pièces jointes via WebSocket est complexe
        # et nécessiterait une logique supplémentaire pour le téléchargement des fichiers
        
        # Mettre à jour la date de dernière modification de la conversation
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        
        return message

    @database_sync_to_async
    def mark_message_read(self, message_id, user_id):
        """Marque un message comme lu par un utilisateur"""
        try:
            message = Message.objects.get(id=message_id)
            user = User.objects.get(id=user_id)
            MessageRead.objects.get_or_create(message=message, user=user)
            return True
        except (Message.DoesNotExist, User.DoesNotExist):
            return False

    @database_sync_to_async
    def update_user_status(self, user_id, is_online):
        """Met à jour le statut en ligne de l'utilisateur"""
        user = User.objects.get(id=user_id)
        user.is_online = is_online
        user.last_activity = timezone.now()
        user.save(update_fields=['is_online', 'last_activity'])


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consommateur pour les notifications en temps réel
    """
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            # Rejeter la connexion si l'utilisateur n'est pas authentifié
            await self.close()
            return
        
        # Groupe personnalisé pour cet utilisateur
        self.user_group = f'user_{self.user.id}_notifications'
        
        # Rejoindre le groupe de l'utilisateur
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        await self.accept()
        
        # Mettre à jour le statut en ligne de l'utilisateur
        await self.update_user_status(self.user.id, True)

    async def disconnect(self, close_code):
        # Quitter le groupe de l'utilisateur
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        # Mettre à jour le statut de l'utilisateur
        if hasattr(self, 'user') and not self.user.is_anonymous:
            await self.update_user_status(self.user.id, False)

    async def receive(self, text_data):
        # Ce consommateur ne traite pas les messages entrants
        # Il sert uniquement à envoyer des notifications à l'utilisateur
        pass

    async def notification(self, event):
        """Envoyer une notification au client WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

    @database_sync_to_async
    def update_user_status(self, user_id, is_online):
        """Met à jour le statut en ligne de l'utilisateur"""
        user = User.objects.get(id=user_id)
        user.is_online = is_online
        user.last_activity = timezone.now()
        user.save(update_fields=['is_online', 'last_activity'])