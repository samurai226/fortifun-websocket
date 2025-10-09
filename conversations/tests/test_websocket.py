# conversations/tests/test_websocket.py

import json
import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from channels.db import database_sync_to_async
from .consumers import ChatConsumer, MainChatConsumer, NotificationConsumer
from .models import Conversation, Message

User = get_user_model()

class WebSocketTestCase(TestCase):
    """Base test case for WebSocket functionality"""
    
    @database_sync_to_async
    def create_user(self, username='testuser', email='test@example.com'):
        """Create a test user"""
        return User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
    
    @database_sync_to_async
    def create_conversation(self, user1, user2):
        """Create a test conversation"""
        conversation = Conversation.objects.create()
        conversation.participants.add(user1, user2)
        return conversation

class TestMainChatConsumer(WebSocketTestCase):
    """Test the main chat consumer for general notifications"""
    
    async def test_connect_with_jwt_token(self):
        """Test WebSocket connection with JWT token"""
        user = await self.create_user()
        
        # Create JWT token (simplified for testing)
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        
        communicator = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            f"/ws/chat/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_connect_without_authentication(self):
        """Test WebSocket connection without authentication"""
        communicator = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            "/ws/chat/"
        )
        
        connected, subprotocol = await communicator.connect()
        # Should still connect but with anonymous user
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_ping_pong(self):
        """Test ping-pong functionality"""
        user = await self.create_user()
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        
        communicator = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            f"/ws/chat/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send ping
        await communicator.send_json_to({
            "type": "ping"
        })
        
        # Should receive pong
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "pong")
        self.assertIn("timestamp", response)
        
        await communicator.disconnect()
    
    async def test_subscribe_to_message_type(self):
        """Test subscribing to specific message types"""
        user = await self.create_user()
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        
        communicator = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            f"/ws/chat/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Subscribe to match notifications
        await communicator.send_json_to({
            "type": "subscribe",
            "subscription_type": "match_notifications"
        })
        
        # Should receive acknowledgment (implementation dependent)
        # This would depend on the actual implementation
        
        await communicator.disconnect()

class TestChatConsumer(WebSocketTestCase):
    """Test the conversation-specific chat consumer"""
    
    async def test_connect_to_conversation(self):
        """Test connecting to a specific conversation"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        conversation = await self.create_conversation(user1, user2)
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user1)
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_connect_to_conversation_unauthorized(self):
        """Test connecting to conversation user is not part of"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        user3 = await self.create_user('user3', 'user3@example.com')
        conversation = await self.create_conversation(user1, user2)
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user3)  # user3 is not part of conversation
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        # Should not connect due to authorization check
        self.assertFalse(connected)
    
    async def test_send_message(self):
        """Test sending a message through WebSocket"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        conversation = await self.create_conversation(user1, user2)
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user1)
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a message
        await communicator.send_json_to({
            "type": "message",
            "content": "Hello, this is a test message!"
        })
        
        # Should receive the message back
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "message")
        self.assertIn("message", response)
        self.assertEqual(response["message"]["content"], "Hello, this is a test message!")
        
        await communicator.disconnect()
    
    async def test_typing_indicator(self):
        """Test typing indicator functionality"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        conversation = await self.create_conversation(user1, user2)
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user1)
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send typing indicator
        await communicator.send_json_to({
            "type": "typing",
            "is_typing": True
        })
        
        # Should receive typing indicator back
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "typing")
        self.assertEqual(response["is_typing"], True)
        self.assertEqual(response["username"], user1.username)
        
        await communicator.disconnect()
    
    async def test_read_receipt(self):
        """Test read receipt functionality"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        conversation = await self.create_conversation(user1, user2)
        
        # Create a message first
        message = await database_sync_to_async(Message.objects.create)(
            conversation=conversation,
            sender=user2,
            content="Test message for read receipt"
        )
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user1)
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send read receipt
        await communicator.send_json_to({
            "type": "read_receipt",
            "message_id": message.id
        })
        
        # Should receive read receipt back
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "read_receipt")
        self.assertEqual(response["message_id"], message.id)
        self.assertEqual(response["user_id"], user1.id)
        
        await communicator.disconnect()

class TestNotificationConsumer(WebSocketTestCase):
    """Test the notification consumer"""
    
    async def test_connect_to_notifications(self):
        """Test connecting to notifications"""
        user = await self.create_user()
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            f"/ws/notifications/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_receive_notification(self):
        """Test receiving a notification"""
        user = await self.create_user()
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken.for_user(user)
        
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            f"/ws/notifications/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a notification to the user's group
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            f'user_{user.id}_notifications',
            {
                'type': 'notification',
                'notification': {
                    'type': 'test_notification',
                    'message': 'This is a test notification',
                    'timestamp': '2024-01-01T00:00:00Z'
                }
            }
        )
        
        # Should receive the notification
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "notification")
        self.assertIn("notification", response)
        self.assertEqual(response["notification"]["type"], "test_notification")
        
        await communicator.disconnect()

class TestWebSocketIntegration(WebSocketTestCase):
    """Integration tests for WebSocket functionality"""
    
    async def test_match_notification_flow(self):
        """Test the complete match notification flow"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        
        from rest_framework_simplejwt.tokens import AccessToken
        token1 = AccessToken.for_user(user1)
        token2 = AccessToken.for_user(user2)
        
        # Connect both users to main chat
        communicator1 = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            f"/ws/chat/?token={token1}"
        )
        communicator2 = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            f"/ws/chat/?token={token2}"
        )
        
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        
        self.assertTrue(connected1)
        self.assertTrue(connected2)
        
        # Simulate a match notification
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        match_data = {
            'id': 1,
            'user': {
                'id': user2.id,
                'username': user2.username,
                'profile_picture': None
            },
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        # Send match notification to user1
        await channel_layer.group_send(
            f'user_{user1.id}_notifications',
            {
                'type': 'match_notification',
                'data': {
                    'type': 'new_match',
                    'match': match_data
                }
            }
        )
        
        # User1 should receive the match notification
        response = await communicator1.receive_json_from()
        self.assertEqual(response["type"], "new_match")
        self.assertIn("data", response)
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    async def test_conversation_creation_after_match(self):
        """Test that conversations are created when users match"""
        user1 = await self.create_user('user1', 'user1@example.com')
        user2 = await self.create_user('user2', 'user2@example.com')
        
        # Simulate match creation (this would normally happen in the matching views)
        from matching.models import Match
        match = await database_sync_to_async(Match.objects.create)(
            user1=user1,
            user2=user2,
            is_active=True
        )
        
        # Check that conversation was created
        conversations = await database_sync_to_async(list)(
            Conversation.objects.filter(participants=user1).filter(participants=user2)
        )
        
        self.assertEqual(len(conversations), 1)
        conversation = conversations[0]
        
        # Check that welcome message was created
        messages = await database_sync_to_async(list)(
            Message.objects.filter(conversation=conversation)
        )
        
        self.assertEqual(len(messages), 1)
        self.assertIn("matché", messages[0].content.lower())




