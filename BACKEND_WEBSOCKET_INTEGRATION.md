# Backend WebSocket Integration Documentation

## 🚀 **Overview**

This document describes the complete WebSocket integration implemented in the Django backend to support real-time chat and match notifications for the Flutter frontend.

## 📋 **Components Implemented**

### 1. **WebSocket Consumers**

#### MainChatConsumer (`/ws/chat/`)
- **Purpose**: Main WebSocket endpoint for general chat functionality
- **Authentication**: JWT token via query parameter
- **Features**:
  - User online status management
  - Match notifications
  - Conversation updates
  - Message notifications
  - Typing indicators

#### ChatConsumer (`/ws/conversations/{id}/`)
- **Purpose**: Conversation-specific WebSocket for real-time messaging
- **Authentication**: JWT token via query parameter
- **Features**:
  - Real-time message delivery
  - Typing indicators
  - Read receipts
  - User status updates

#### NotificationConsumer (`/ws/notifications/`)
- **Purpose**: General notifications for users
- **Authentication**: JWT token via query parameter
- **Features**:
  - Match notifications
  - System notifications

### 2. **Authentication Middleware**

#### AppwriteAuthMiddleware
- **JWT Support**: Primary authentication method
- **Appwrite Fallback**: Legacy support for Appwrite user IDs
- **Token Location**: Query parameter `?token=jwt_token`
- **Security**: Validates JWT signatures and expiration

### 3. **API Endpoints Enhanced**

#### Matching APIs
- **LikeView**: Enhanced with WebSocket notifications for matches
- **RecentMatchesView**: New endpoint for chat integration
- **Auto-conversation creation**: Conversations created automatically on match

#### Chat APIs
- **MessageViewSet**: Enhanced with WebSocket notifications
- **ConversationViewSet**: Real-time conversation updates

## 🔧 **WebSocket Message Types**

### From Client to Server

```json
{
  "type": "ping",
  "timestamp": "2024-01-01T00:00:00Z"
}

{
  "type": "subscribe",
  "subscription_type": "matches"
}

{
  "type": "message",
  "content": "Hello!",
  "attachment": "optional_url"
}

{
  "type": "typing",
  "is_typing": true
}

{
  "type": "read_receipt",
  "message_id": 123
}
```

### From Server to Client

```json
{
  "type": "pong",
  "timestamp": "2024-01-01T00:00:00Z"
}

{
  "type": "new_match",
  "data": {
    "type": "new_match",
    "match": {
      "id": 1,
      "user": {
        "id": 2,
        "username": "jane_doe",
        "profile_picture": "https://...",
        "first_name": "Jane",
        "last_name": "Doe"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}

{
  "type": "conversation_update",
  "event": "conversation.create",
  "data": {
    "id": 1,
    "participants": [...],
    "created_at": "2024-01-01T00:00:00Z"
  }
}

{
  "type": "new_message",
  "conversation_id": 1,
  "message": {
    "id": 123,
    "sender": {
      "id": 1,
      "username": "john_doe",
      "profile_picture": "https://..."
    },
    "content": "Hello!",
    "created_at": "2024-01-01T00:00:00Z",
    "is_read": false
  }
}

{
  "type": "typing_indicator",
  "conversation_id": 1,
  "is_typing": true,
  "user_name": "Jane Doe"
}
```

## 🛠 **Setup Instructions**

### 1. **Install Dependencies**

```bash
pip install channels channels-redis PyJWT
```

### 2. **Update Settings**

```python
# settings.py
INSTALLED_APPS = [
    'channels',
    'conversations',
    'matching',
    # ... other apps
]

ASGI_APPLICATION = 'chat_api.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 3. **Run Redis Server**

```bash
redis-server
```

### 4. **Start Django with ASGI**

```bash
# Development
python manage.py runserver

# Production with Daphne
daphne -b 0.0.0.0 -p 8000 chat_api.asgi:application
```

## 🧪 **Testing**

### 1. **WebSocket Test Script**

```bash
python test_websocket_integration.py
```

### 2. **Manual Testing with WebSocket Client**

```javascript
// Connect to main chat WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat/?token=your_jwt_token');

ws.onopen = () => {
    console.log('Connected to WebSocket');
    
    // Send ping
    ws.send(JSON.stringify({type: 'ping'}));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## 🔄 **Integration Flow**

### 1. **User Likes Profile**
1. Frontend calls `POST /api/matching/like/`
2. Backend checks for mutual like
3. If match created:
   - Creates conversation automatically
   - Sends WebSocket notification to both users
   - Updates match lists

### 2. **User Sends Message**
1. Frontend calls `POST /api/conversations/{id}/messages/`
2. Backend saves message to database
3. Sends WebSocket notification to conversation participants
4. Updates conversation timestamp

### 3. **Real-time Updates**
1. Frontend connects to WebSocket with JWT token
2. Backend authenticates user
3. User joins notification groups
4. Real-time updates sent via WebSocket

## 📊 **Performance Considerations**

### 1. **Redis Channel Layer**
- Handles message routing efficiently
- Supports horizontal scaling
- Persistent message queuing

### 2. **Database Optimization**
- Async database operations
- Connection pooling
- Query optimization for real-time data

### 3. **WebSocket Management**
- Automatic reconnection handling
- Connection cleanup on disconnect
- Rate limiting for message sending

## 🔒 **Security Features**

### 1. **JWT Authentication**
- Token validation on every WebSocket connection
- Automatic token expiration handling
- Secure token transmission

### 2. **Origin Validation**
- Allowed hosts configuration
- CORS protection
- Request validation

### 3. **User Authorization**
- Conversation participation verification
- Message ownership validation
- Permission-based access control

## 🚨 **Error Handling**

### 1. **Connection Errors**
- Automatic reconnection attempts
- Graceful degradation
- Error logging and monitoring

### 2. **Authentication Errors**
- Clear error messages
- Token refresh handling
- Fallback authentication methods

### 3. **Message Errors**
- Validation error responses
- Retry mechanisms
- Offline message queuing

## 📈 **Monitoring and Logging**

### 1. **WebSocket Metrics**
- Connection count
- Message throughput
- Error rates

### 2. **Performance Monitoring**
- Response times
- Database query performance
- Redis channel layer metrics

### 3. **User Activity Tracking**
- Online status tracking
- Message activity logs
- Match creation analytics

## 🔮 **Future Enhancements**

### 1. **Advanced Features**
- Voice/video call signaling
- File sharing via WebSocket
- Push notifications integration

### 2. **Scalability Improvements**
- WebSocket clustering
- Load balancing
- Message persistence

### 3. **Analytics Integration**
- Real-time user behavior tracking
- Match success analytics
- Performance optimization insights

## 📞 **Support and Troubleshooting**

### Common Issues

1. **WebSocket Connection Failed**
   - Check JWT token validity
   - Verify Redis server is running
   - Check firewall settings

2. **Messages Not Received**
   - Verify user is in conversation
   - Check WebSocket connection status
   - Validate message format

3. **Authentication Errors**
   - Check JWT secret key configuration
   - Verify token expiration
   - Check user permissions

### Debug Commands

```bash
# Check Redis connection
redis-cli ping

# Monitor WebSocket connections
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> print(channel_layer.group_channels('user_1_notifications'))
```

This integration provides a robust, scalable foundation for real-time chat and match notifications in your dating app!



