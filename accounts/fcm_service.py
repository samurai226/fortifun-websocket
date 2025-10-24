# accounts/fcm_service.py

import json
import requests
from django.conf import settings
from django.utils import timezone
from .models import DeviceToken, User

class FCMService:
    """Service for sending Firebase Cloud Messaging notifications"""
    
    def __init__(self):
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        
    def send_notification(self, user_id, title, body, data=None, notification_type='generic'):
        """
        Send push notification to a user
        
        Args:
            user_id: ID of the user to send notification to
            title: Notification title
            body: Notification body
            data: Additional data payload
            notification_type: Type of notification for routing
        """
        try:
            user = User.objects.get(id=user_id)
            device_tokens = user.get_active_device_tokens()
            
            if not device_tokens.exists():
                print(f"No active device tokens found for user {user_id}")
                return False
            
            # Prepare notification payload
            notification_payload = {
                'title': title,
                'body': body,
            }
            
            # Prepare data payload
            data_payload = {
                'type': notification_type,
                'timestamp': timezone.now().isoformat(),
                'user_id': str(user_id),
            }
            
            if data:
                data_payload.update(data)
            
            # Send to each device token
            success_count = 0
            for device_token in device_tokens:
                if self._send_to_device(device_token.device_token, notification_payload, data_payload):
                    success_count += 1
                    # Update last_used timestamp
                    device_token.last_used = timezone.now()
                    device_token.save(update_fields=['last_used'])
            
            print(f"Sent notification to {success_count}/{device_tokens.count()} devices for user {user_id}")
            return success_count > 0
            
        except User.DoesNotExist:
            print(f"User {user_id} not found")
            return False
        except Exception as e:
            print(f"Error sending notification to user {user_id}: {e}")
            return False
    
    def _send_to_device(self, device_token, notification, data):
        """Send notification to a specific device token"""
        if not self.server_key:
            print("FCM server key not configured")
            return False
        
        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'to': device_token,
            'notification': notification,
            'data': data,
            'priority': 'high',
        }
        
        try:
            response = requests.post(
                self.fcm_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', 0) > 0:
                    return True
                else:
                    print(f"FCM send failed: {result}")
                    return False
            else:
                print(f"FCM request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False
    
    def send_message_notification(self, user_id, sender_name, message_content, conversation_id):
        """Send new message notification"""
        title = f"Message from {sender_name}"
        body = message_content[:100] + "..." if len(message_content) > 100 else message_content
        
        data = {
            'conversation_id': str(conversation_id),
            'sender_name': sender_name,
        }
        
        return self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            notification_type='new_message'
        )
    
    def send_match_notification(self, user_id, match_name, match_id):
        """Send new match notification"""
        title = "🎉 Nouveau Match!"
        body = f"Vous avez matché avec {match_name}!"
        
        data = {
            'match_id': str(match_id),
            'match_name': match_name,
        }
        
        return self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            notification_type='new_match'
        )
    
    def send_like_notification(self, user_id, liker_name, liker_id):
        """Send like notification"""
        title = "💖 Nouveau Like!"
        body = f"{liker_name} vous a aimé!"
        
        data = {
            'liker_id': str(liker_id),
            'liker_name': liker_name,
        }
        
        return self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            notification_type='new_like'
        )
    
    def send_system_notification(self, user_id, title, body, data=None):
        """Send system notification"""
        return self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            notification_type='system'
        )
    
    def cleanup_inactive_tokens(self, days_inactive=30):
        """Remove device tokens that haven't been used for specified days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_inactive)
        inactive_tokens = DeviceToken.objects.filter(
            last_used__lt=cutoff_date,
            is_active=True
        )
        
        count = inactive_tokens.count()
        inactive_tokens.update(is_active=False)
        
        print(f"Deactivated {count} inactive device tokens")
        return count

# Global FCM service instance
fcm_service = FCMService()


