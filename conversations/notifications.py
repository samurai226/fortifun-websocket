# conversations/notifications.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

def send_notification(user_id, notification_type, **kwargs):
    """
    Envoie une notification à un utilisateur spécifique via WebSocket
    
    Args:
        user_id: ID de l'utilisateur destinataire
        notification_type: Type de notification (message, match, etc.)
        **kwargs: Données supplémentaires de la notification
    """
    channel_layer = get_channel_layer()
    
    notification = {
        'type': notification_type,
        'timestamp': timezone.now().isoformat(),
        **kwargs
    }
    
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}_notifications',
        {
            'type': 'notification',
            'notification': notification
        }
    )

def notify_new_message(user_id, message_data):
    """
    Notifie un utilisateur d'un nouveau message
    """
    send_notification(
        user_id=user_id,
        notification_type='new_message',
        message=message_data
    )

def notify_new_match(user_id, match_data):
    """
    Notifie un utilisateur d'un nouveau match
    """
    send_notification(
        user_id=user_id,
        notification_type='new_match',
        match=match_data
    )

def notify_like(user_id, liker_data):
    """
    Notifie un utilisateur qu'il a reçu un like
    """
    send_notification(
        user_id=user_id,
        notification_type='new_like',
        liker=liker_data
    )