#!/usr/bin/env python3
"""
Test script for WebSocket integration with Flutter frontend
"""

import asyncio
import websockets
import json
import jwt
from datetime import datetime, timedelta

# Test configuration
WS_URL = "ws://localhost:8000/ws/chat/"
JWT_SECRET = "your-secret-key"  # Should match Django SECRET_KEY

def create_test_jwt(user_id=1):
    """Create a test JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

async def test_websocket_connection():
    """Test WebSocket connection and message handling"""
    token = create_test_jwt()
    url = f"{WS_URL}?token={token}"
    
    print(f"Connecting to: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send ping
            ping_message = {
                "type": "ping"
            }
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping")
            
            # Wait for pong response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get('type') == 'pong':
                print("✅ Ping/Pong working correctly")
            
            # Test subscription to match notifications
            subscribe_message = {
                "type": "subscribe",
                "subscription_type": "matches"
            }
            await websocket.send(json.dumps(subscribe_message))
            print("📤 Subscribed to match notifications")
            
            # Keep connection alive for a bit
            await asyncio.sleep(5)
            
            print("✅ WebSocket test completed successfully")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

async def test_conversation_websocket():
    """Test conversation-specific WebSocket"""
    token = create_test_jwt()
    conversation_id = 1
    url = f"ws://localhost:8000/ws/conversations/{conversation_id}/?token={token}"
    
    print(f"Connecting to conversation WebSocket: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to conversation WebSocket")
            
            # Send a test message
            message = {
                "type": "message",
                "content": "Hello from test client!"
            }
            await websocket.send(json.dumps(message))
            print("📤 Sent test message")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            print("✅ Conversation WebSocket test completed")
            
    except Exception as e:
        print(f"❌ Conversation WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket Integration")
    print("=" * 50)
    
    # Test main chat WebSocket
    print("\n1. Testing Main Chat WebSocket...")
    asyncio.run(test_websocket_connection())
    
    # Test conversation WebSocket
    print("\n2. Testing Conversation WebSocket...")
    asyncio.run(test_conversation_websocket())
    
    print("\n🎉 All tests completed!")



