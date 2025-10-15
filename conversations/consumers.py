# conversations/consumers.py

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from .models import Conversation, Message
from .serializers import MessageSerializer
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

class MainChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        self.room_group_name = f'user_{self.user.id}_notifications'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': timezone.now().isoformat()
            }))

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event))

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        self.room_group_name = f'user_{self.user.id}_notifications'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event))

class ConversationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'conversation_{self.conversation_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Check if user is part of this conversation
        if not await self.is_user_in_conversation():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(text_data_json)

    async def handle_chat_message(self, data):
        message_content = data.get('message', '').strip()
        if not message_content:
            return

        # Create message in database
        message = await self.create_message(message_content)
        
        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': MessageSerializer(message).data
                }
            )

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        
        # Mark message as read
        await self.mark_message_as_read(message_id)

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['message']
        }))

    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def is_user_in_conversation(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            return message
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if message.sender != self.user:
                message.is_read = True
                message.save()
        except Message.DoesNotExist:
            pass

# NEW: Anonymous Chat Consumer for immediate chat after matching
class AnonymousChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'anonymous_chat_{self.room_id}'
        
        # No authentication required for anonymous chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': 'Connected to anonymous chat room',
            'room_id': self.room_id,
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'user_join':
                await self.handle_user_join(data)
            elif message_type == 'user_leave':
                await self.handle_user_leave(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def handle_chat_message(self, data):
        message_content = data.get('message', '').strip()
        sender_name = data.get('sender_name', 'Anonymous')
        sender_id = data.get('sender_id', 'anonymous')
        
        if not message_content:
            return

        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_name': sender_name,
                'sender_id': sender_id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        sender_name = data.get('sender_name', 'Anonymous')
        sender_id = data.get('sender_id', 'anonymous')
        
        # Broadcast typing indicator to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'sender_name': sender_name,
                'sender_id': sender_id,
                'is_typing': is_typing
            }
        )

    async def handle_user_join(self, data):
        sender_name = data.get('sender_name', 'Anonymous')
        sender_id = data.get('sender_id', 'anonymous')
        
        # Broadcast user join to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'sender_name': sender_name,
                'sender_id': sender_id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_user_leave(self, data):
        sender_name = data.get('sender_name', 'Anonymous')
        sender_id = data.get('sender_id', 'anonymous')
        
        # Broadcast user leave to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'sender_name': sender_name,
                'sender_id': sender_id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_name': event['sender_name'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'sender_name': event['sender_name'],
            'sender_id': event['sender_id'],
            'is_typing': event['is_typing']
        }))

    async def user_join(self, event):
        # Send user join notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'sender_name': event['sender_name'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    async def user_leave(self, event):
        # Send user leave notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'sender_name': event['sender_name'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))