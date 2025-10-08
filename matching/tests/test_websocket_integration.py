# matching/tests/test_websocket_integration.py

import json
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from matching.views import ChatConsumer, MainChatConsumer
from matching.models import Match
from conversations.models import Conversation, Message

User = get_user_model()

class MatchingWebSocketIntegrationTest(TestCase):
    """Test WebSocket integration with matching functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Get JWT tokens
        self.token1 = AccessToken.for_user(self.user1)
        self.token2 = AccessToken.for_user(self.user2)
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user1)
    
    async def test_like_creates_match_with_websocket_notification(self):
        """Test that liking a user creates a match and sends WebSocket notification"""
        # First, user2 likes user1
        self.client.force_authenticate(user=self.user2)
        like_response = self.client.post('/api/v1/matching/like/', {
            'user_id': self.user1.id
        })
        self.assertEqual(like_response.status_code, 201)
        self.assertFalse(like_response.data.get('is_match', False))
        
        # Connect user1 to WebSocket to receive notifications
        communicator = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            f"/ws/chat/?token={self.token1}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Now user1 likes user2 back (this should create a match)
        self.client.force_authenticate(user=self.user1)
        match_response = self.client.post('/api/v1/matching/like/', {
            'user_id': self.user2.id
        })
        
        self.assertEqual(match_response.status_code, 201)
        self.assertTrue(match_response.data.get('is_match', False))
        
        # User1 should receive a WebSocket notification about the match
        try:
            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "new_match")
            self.assertIn("data", response)
        except Exception as e:
            self.fail(f"Expected WebSocket notification but got: {e}")
        
        await communicator.disconnect()
    
    async def test_conversation_created_after_match(self):
        """Test that a conversation is created when users match"""
        # Create a match manually
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            is_active=True
        )
        
        # Check that conversation was created
        conversations = Conversation.objects.filter(
            participants=self.user1
        ).filter(
            participants=self.user2
        )
        
        self.assertEqual(conversations.count(), 1)
        conversation = conversations.first()
        
        # Check that welcome message was created
        messages = Message.objects.filter(conversation=conversation)
        self.assertEqual(messages.count(), 1)
        
        welcome_message = messages.first()
        self.assertIn("matché", welcome_message.content.lower())
        self.assertEqual(welcome_message.sender, self.user1)
    
    async def test_websocket_message_delivery(self):
        """Test that messages are delivered via WebSocket"""
        # Create a conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Connect both users to the conversation WebSocket
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token1}"
        )
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token2}"
        )
        
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        
        self.assertTrue(connected1)
        self.assertTrue(connected2)
        
        # User1 sends a message
        await communicator1.send_json_to({
            "type": "message",
            "content": "Hello from user1!"
        })
        
        # Both users should receive the message
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        
        self.assertEqual(response1["type"], "message")
        self.assertEqual(response2["type"], "message")
        self.assertEqual(response1["message"]["content"], "Hello from user1!")
        self.assertEqual(response2["message"]["content"], "Hello from user1!")
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    async def test_typing_indicators(self):
        """Test typing indicators work across WebSocket"""
        # Create a conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        # Connect both users
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token1}"
        )
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token2}"
        )
        
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        
        self.assertTrue(connected1)
        self.assertTrue(connected2)
        
        # User1 starts typing
        await communicator1.send_json_to({
            "type": "typing",
            "is_typing": True
        })
        
        # User2 should receive the typing indicator
        response = await communicator2.receive_json_from()
        self.assertEqual(response["type"], "typing")
        self.assertEqual(response["is_typing"], True)
        self.assertEqual(response["username"], self.user1.username)
        
        # User1 stops typing
        await communicator1.send_json_to({
            "type": "typing",
            "is_typing": False
        })
        
        # User2 should receive the stop typing indicator
        response = await communicator2.receive_json_from()
        self.assertEqual(response["type"], "typing")
        self.assertEqual(response["is_typing"], False)
        self.assertEqual(response["username"], self.user1.username)
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    async def test_read_receipts(self):
        """Test read receipts work via WebSocket"""
        # Create a conversation and message
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            content="Test message for read receipt"
        )
        
        # Connect both users
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token1}"
        )
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token2}"
        )
        
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        
        self.assertTrue(connected1)
        self.assertTrue(connected2)
        
        # User1 marks message as read
        await communicator1.send_json_to({
            "type": "read_receipt",
            "message_id": message.id
        })
        
        # Both users should receive the read receipt
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        
        self.assertEqual(response1["type"], "read_receipt")
        self.assertEqual(response2["type"], "read_receipt")
        self.assertEqual(response1["message_id"], message.id)
        self.assertEqual(response2["message_id"], message.id)
        self.assertEqual(response1["user_id"], self.user1.id)
        self.assertEqual(response2["user_id"], self.user1.id)
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    def test_recent_matches_api(self):
        """Test the recent matches API endpoint"""
        # Create some matches
        Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            is_active=True
        )
        
        # Get recent matches
        response = self.client.get('/api/v1/matching/recent-matches/')
        self.assertEqual(response.status_code, 200)
        
        matches = response.data
        self.assertIsInstance(matches, list)
        self.assertEqual(len(matches), 1)
        
        match_data = matches[0]
        self.assertIn('id', match_data)
        self.assertIn('username', match_data)
        self.assertIn('first_name', match_data)
        self.assertIn('profile_picture', match_data)
        self.assertIn('is_online', match_data)
        self.assertIn('match_created_at', match_data)
    
    async def test_websocket_connection_without_auth(self):
        """Test WebSocket connection without authentication"""
        communicator = WebsocketCommunicator(
            MainChatConsumer.as_asgi(),
            "/ws/chat/"
        )
        
        connected, subprotocol = await communicator.connect()
        # Should still connect but with limited functionality
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        # Try to connect to non-existent conversation
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/99999/?token={self.token1}"
        )
        
        connected, subprotocol = await communicator.connect()
        # Should not connect due to conversation not existing
        self.assertFalse(connected)
    
    async def test_websocket_message_validation(self):
        """Test WebSocket message validation"""
        # Create a conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/conversations/{conversation.id}/?token={self.token1}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send invalid message (missing content)
        await communicator.send_json_to({
            "type": "message"
            # Missing content field
        })
        
        # Should not crash and should handle gracefully
        # (exact behavior depends on implementation)
        
        await communicator.disconnect()


