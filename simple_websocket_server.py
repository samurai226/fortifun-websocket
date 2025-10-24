#!/usr/bin/env python3
"""
Simple WebSocket Server for Testing
Mimics the Django WebSocket functionality for quick testing
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

class SimpleWebSocketServer:
    def __init__(self, host="127.0.0.1", port=8002):
        self.host = host
        self.port = port
        self.clients = set()
        self.rooms = {}
    
    async def register_client(self, websocket, path):
        """Register a new client"""
        self.clients.add(websocket)
        print(f"✅ Client connected: {websocket.remote_address}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'welcome',
            'message': 'Connected to test WebSocket server',
            'timestamp': datetime.now().isoformat(),
            'path': path
        }))
    
    async def unregister_client(self, websocket):
        """Unregister a client"""
        self.clients.discard(websocket)
        print(f"❌ Client disconnected: {websocket.remote_address}")
    
    async def handle_message(self, websocket, message):
        """Handle incoming message"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            print(f"📨 Received {message_type}: {data}")
            
            if message_type == 'ping':
                # Respond to ping
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat(),
                    'original_message': data
                }))
            
            elif message_type == 'chat_message':
                # Echo chat message
                await websocket.send(json.dumps({
                    'type': 'chat_message',
                    'message': f"Echo: {data.get('message', '')}",
                    'sender_name': 'Server',
                    'sender_id': 'server',
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'typing':
                # Echo typing indicator
                await websocket.send(json.dumps({
                    'type': 'typing_indicator',
                    'sender_name': 'Server',
                    'sender_id': 'server',
                    'is_typing': data.get('is_typing', False),
                    'timestamp': datetime.now().isoformat()
                }))
            
            else:
                # Echo unknown message type
                await websocket.send(json.dumps({
                    'type': 'echo',
                    'original_message': data,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            # Echo non-JSON messages
            await websocket.send(json.dumps({
                'type': 'echo',
                'message': f"Echo: {message}",
                'timestamp': datetime.now().isoformat()
            }))
    
    async def handle_client(self, websocket):
        """Handle a client connection"""
        # For simplicity, we'll use a default path since we can't easily extract it
        path = '/'
        await self.register_client(websocket, path)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        print(f"🚀 Starting WebSocket server on {self.host}:{self.port}")
        print("📋 Available endpoints:")
        print("   - ws://127.0.0.1:8002/ws/chat/")
        print("   - ws://127.0.0.1:8002/ws/anonymous-chat/test_room/")
        print("   - ws://127.0.0.1:8002/ws/conversations/1/")
        print("   - ws://127.0.0.1:8002/ws/notifications/")
        print("\n🔧 Test with the browser client or Python client")
        print("=" * 60)
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever

async def main():
    """Main function"""
    server = SimpleWebSocketServer()
    await server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
