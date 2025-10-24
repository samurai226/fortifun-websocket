# Add this to the existing User model or create a new DeviceToken model

from django.db import models
from django.contrib.auth.models import AbstractUser

class DeviceToken(models.Model):
    """Model to store FCM device tokens for push notifications"""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='device_tokens')
    device_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=50, choices=[
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ])
    app_version = models.CharField(max_length=20, default='1.0.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'device_tokens'
        unique_together = ['user', 'device_token']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} ({self.device_token[:20]}...)"

# Add this method to the existing User model
class User(AbstractUser):
    # ... existing fields ...
    
    def get_active_device_tokens(self):
        """Get all active device tokens for this user"""
        return self.device_tokens.filter(is_active=True)
    
    def get_device_tokens_by_type(self, device_type):
        """Get device tokens for a specific device type"""
        return self.device_tokens.filter(device_type=device_type, is_active=True)