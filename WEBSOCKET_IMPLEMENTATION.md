# WebSocket Implementation Documentation

## Overview

This document describes the complete WebSocket implementation for the FortiFun dating app, including real-time chat, match notifications, and conversation management.

## Architecture

### Frontend (Flutter)
- **RealtimeBus**: Central WebSocket service for Django backend communication
- **MatchChatIntegration**: Service bridging matching and chat modules
- **ChatController**: Manages conversations and real-time messaging
- **MatchingController**: Handles match creation and notifications

### Backend (Django)
- **WebSocket Consumers**: Handle real-time connections
- **JWT Authentication**: Secure WebSocket connections
- **Channel Layers**: Redis-based message routing
- **Auto-conversation Creation**: Creates chats when users match

## WebSocket Endpoints

### Main Chat WebSocket
```
ws://localhost:8000/ws/chat/?token=<jwt_token>
```
- General notifications and match alerts
- User status updates
- Ping/pong for connection health

### Conversation WebSocket
```
ws://localhost:8000/ws/conversations/<conversation_id>/?token=<jwt_token>
```
- Real-time messaging
- Typing indicators
- Read receipts
- User status in conversation

### Notifications WebSocket
```
ws://localhost:8000/ws/notifications/?token=<jwt_token>
```
- Match notifications
- System alerts
- User-specific notifications

## Message Types

### From Client to Server

#### Main Chat
```json
{
  "type": "ping"
}
```

```json
{
  "type": "subscribe",
  "subscription_type": "match_notifications"
}
```

#### Conversation
```json
{
  "type": "message",
  "content": "Hello, how are you?"
}
```

```json
{
  "type": "typing",
  "is_typing": true
}
```

```json
{
  "type": "read_receipt",
  "message_id": 123
}
```

### From Server to Client

#### Match Notifications
```json
{
  "type": "new_match",
  "data": {
    "type": "new_match",
    "match": {
      "id": 1,
      "user": {
        "id": 2,
        "username": "jane_doe",
        "profile_picture": "https://example.com/photo.jpg"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

#### Chat Messages
```json
{
  "type": "message",
  "message": {
    "id": 123,
    "conversation_id": 456,
    "sender": {
      "id": 1,
      "username": "john_doe",
      "profile_picture": "https://example.com/photo.jpg"
    },
    "content": "Hello, how are you?",
    "created_at": "2024-01-01T00:00:00Z",
    "is_read": false,
    "attachment": null
  }
}
```

#### Typing Indicators
```json
{
  "type": "typing",
  "user_id": 1,
  "username": "john_doe",
  "is_typing": true
}
```

#### Read Receipts
```json
{
  "type": "read_receipt",
  "message_id": 123,
  "user_id": 1,
  "username": "john_doe",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Authentication

WebSocket connections use JWT tokens passed as query parameters:

```
ws://localhost:8000/ws/chat/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

The JWT token is validated by the `AppwriteAuthMiddleware` which:
1. Extracts the token from query parameters
2. Decodes and validates the JWT
3. Sets the user in the WebSocket scope
4. Falls back to Appwrite headers if JWT fails

## Channel Layers

### Development
Uses in-memory channel layer for local development.

### Production
Uses Redis channel layer for scalability:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.getenv('REDIS_URL', 'redis://localhost:6379')],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}
```

## Consumer Classes

### MainChatConsumer
Handles general WebSocket connections and notifications.

**Key Features:**
- JWT authentication
- Ping/pong health checks
- Match notifications
- User status updates

### ChatConsumer
Handles conversation-specific WebSocket connections.

**Key Features:**
- Conversation authorization
- Real-time messaging
- Typing indicators
- Read receipts
- User status in conversations

### NotificationConsumer
Handles user-specific notifications.

**Key Features:**
- User notification groups
- Match alerts
- System notifications

## Auto-Conversation Creation

When users match, a conversation is automatically created:

1. **Match Creation**: Users like each other
2. **Match Model**: `Match` object created in database
3. **Conversation Creation**: `Conversation` object created
4. **Welcome Message**: Initial message added
5. **WebSocket Notification**: Both users notified

```python
def create_conversation_for_match(user1, user2):
    """Create a conversation when users match"""
    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(
        participants=user1
    ).filter(
        participants=user2
    ).first()
    
    if existing_conversation:
        return existing_conversation
    
    # Create new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(user1, user2)
    
    # Create initial welcome message
    welcome_message = Message.objects.create(
        conversation=conversation,
        sender=user1,
        content="Vous avez matché! Commencez la conversation."
    )
    
    return conversation
```

## Error Handling

### Connection Errors
- Invalid JWT tokens are rejected
- Unauthorized conversation access is blocked
- Network errors trigger reconnection

### Message Errors
- Invalid message formats are ignored
- Database errors are logged and handled gracefully
- Missing conversations return appropriate errors

### Reconnection Logic
The Flutter `RealtimeBus` includes automatic reconnection:
- Exponential backoff for failed connections
- Maximum retry attempts (5)
- Token refresh on 401 errors

## Testing

### Unit Tests
Test individual consumer functionality:
```bash
python manage.py test conversations.tests.test_websocket
```

### Integration Tests
Test complete match-to-chat flow:
```bash
python manage.py test matching.tests.test_websocket_integration
```

### Manual Testing
Run the comprehensive test suite:
```bash
python run_websocket_tests.py
```

## Performance Considerations

### Redis Configuration
- **Capacity**: 1500 messages per channel
- **Expiry**: 60 seconds for message retention
- **Hosts**: Single Redis instance (can be clustered)

### Message Batching
- Messages are sent immediately for real-time feel
- No batching implemented (can be added for high volume)

### Connection Limits
- No explicit connection limits set
- Django Channels handles connection management
- Redis capacity limits apply

## Security

### JWT Validation
- Tokens are validated on every connection
- Invalid tokens are rejected immediately
- Token expiration is respected

### Authorization
- Users can only access their own conversations
- Conversation participants are verified
- WebSocket groups are user-specific

### Rate Limiting
- No WebSocket-specific rate limiting
- API rate limiting applies to message creation
- Consider adding WebSocket rate limiting for production

## Monitoring

### Logging
All WebSocket events are logged:
- Connection/disconnection events
- Message sending/receiving
- Authentication failures
- Error conditions

### Metrics
Track key metrics:
- Active WebSocket connections
- Messages per second
- Authentication success rate
- Error rates by type

## Deployment

### Environment Variables
```bash
# Required
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key

# Optional
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```

### Dependencies
```bash
pip install channels
pip install channels-redis
pip install djangorestframework-simplejwt
```

### Production Setup
1. Configure Redis cluster
2. Set up load balancer for WebSocket connections
3. Configure SSL/TLS for WSS connections
4. Set up monitoring and alerting
5. Configure backup and recovery

## Troubleshooting

### Common Issues

#### Connection Refused
- Check Redis is running
- Verify REDIS_URL configuration
- Check firewall settings

#### Authentication Failures
- Verify JWT token is valid
- Check token expiration
- Ensure user exists in database

#### Messages Not Delivered
- Check channel layer configuration
- Verify user is in correct WebSocket group
- Check for database errors

#### High Memory Usage
- Monitor Redis memory usage
- Adjust channel layer capacity
- Consider message batching

### Debug Commands
```bash
# Check Redis connection
redis-cli ping

# Monitor Redis activity
redis-cli monitor

# Check Django channels
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> print(channel_layer)
```

## Future Enhancements

### Planned Features
- Message encryption
- File sharing via WebSocket
- Voice/video call signaling
- Push notifications integration
- Message search and filtering
- Group conversations
- Message reactions and replies

### Performance Improvements
- Message batching for high volume
- Connection pooling
- Message compression
- CDN integration for media

### Security Enhancements
- End-to-end encryption
- Message signing
- Rate limiting per connection
- IP-based connection limits
- Audit logging

## API Reference

### WebSocket URLs
- `ws://domain/ws/chat/` - Main chat notifications
- `ws://domain/ws/conversations/{id}/` - Conversation chat
- `ws://domain/ws/notifications/` - User notifications

### REST API Endpoints
- `GET /api/v1/conversations/` - List conversations
- `POST /api/v1/conversations/` - Create conversation
- `GET /api/v1/conversations/{id}/messages/` - List messages
- `POST /api/v1/conversations/{id}/messages/` - Send message
- `GET /api/v1/matching/recent-matches/` - Recent matches

### Authentication
All WebSocket connections require JWT authentication via query parameter:
```
?token=<jwt_token>
```

All REST API calls require JWT authentication via Authorization header:
```
Authorization: Bearer <jwt_token>
```



