#!/usr/bin/env python
"""
Test runner for WebSocket functionality
Run this script to test the complete WebSocket implementation
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_django():
    """Setup Django environment for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')
    django.setup()

def run_websocket_tests():
    """Run WebSocket-specific tests"""
    setup_django()
    
    # Test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Test patterns for WebSocket functionality
    test_patterns = [
        'conversations.tests.test_websocket',
        'matching.tests.test_websocket_integration',
    ]
    
    print("🧪 Running WebSocket Tests...")
    print("=" * 50)
    
    failures = test_runner.run_tests(test_patterns)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        return False
    else:
        print("\n✅ All WebSocket tests passed!")
        return True

def run_integration_tests():
    """Run integration tests for the complete flow"""
    setup_django()
    
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    # Test the complete match-to-chat flow
    from django.test import TestCase
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import AccessToken
    from matching.models import Match
    from conversations.models import Conversation, Message
    
    User = get_user_model()
    
    class IntegrationTest(TestCase):
        def test_complete_match_to_chat_flow(self):
            """Test the complete flow from match to chat"""
            # Create users
            user1 = User.objects.create_user(
                username='testuser1',
                email='test1@example.com',
                password='testpass123'
            )
            user2 = User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='testpass123'
            )
            
            # Authenticate
            client = APIClient()
            token1 = AccessToken.for_user(user1)
            client.force_authenticate(user=user1)
            
            # User1 likes user2
            like_response = client.post('/api/v1/matching/like/', {
                'user_id': user2.id
            })
            self.assertEqual(like_response.status_code, 201)
            
            # User2 likes user1 back (creates match)
            client.force_authenticate(user=user2)
            match_response = client.post('/api/v1/matching/like/', {
                'user_id': user1.id
            })
            self.assertEqual(match_response.status_code, 201)
            self.assertTrue(match_response.data.get('is_match', False))
            
            # Check that match was created
            match = Match.objects.filter(
                user1=user1, user2=user2, is_active=True
            ).first()
            self.assertIsNotNone(match)
            
            # Check that conversation was created
            conversation = Conversation.objects.filter(
                participants=user1
            ).filter(
                participants=user2
            ).first()
            self.assertIsNotNone(conversation)
            
            # Check that welcome message was created
            welcome_message = Message.objects.filter(
                conversation=conversation
            ).first()
            self.assertIsNotNone(welcome_message)
            self.assertIn("matché", welcome_message.content.lower())
            
            # Test sending a message
            client.force_authenticate(user=user1)
            message_response = client.post(
                f'/api/v1/conversations/{conversation.id}/messages/',
                {
                    'conversation': conversation.id,
                    'content': 'Hello from the test!'
                }
            )
            self.assertEqual(message_response.status_code, 201)
            
            # Test getting conversation messages
            messages_response = client.get(
                f'/api/v1/conversations/{conversation.id}/messages/'
            )
            self.assertEqual(messages_response.status_code, 200)
            self.assertEqual(len(messages_response.data), 2)  # Welcome + test message
            
            # Test getting recent matches
            matches_response = client.get('/api/v1/matching/recent-matches/')
            self.assertEqual(matches_response.status_code, 200)
            self.assertEqual(len(matches_response.data), 1)
            
            match_data = matches_response.data[0]
            self.assertEqual(match_data['id'], user2.id)
            self.assertEqual(match_data['username'], user2.username)
    
    # Run the integration test
    test_case = IntegrationTest()
    test_case.setUp()
    try:
        test_case.test_complete_match_to_chat_flow()
        print("✅ Integration test passed!")
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Starting WebSocket Test Suite")
    print("=" * 50)
    
    # Run WebSocket tests
    websocket_success = run_websocket_tests()
    
    # Run integration tests
    integration_success = run_integration_tests()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"WebSocket Tests: {'✅ PASSED' if websocket_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if websocket_success and integration_success:
        print("\n🎉 All tests passed! WebSocket implementation is working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())



