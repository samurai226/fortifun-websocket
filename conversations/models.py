# conversations/models.py

from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """Modèle pour les conversations entre utilisateurs"""
    
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Conversation {self.id} - {', '.join([user.username for user in self.participants.all()])}"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    """Modèle pour les messages dans une conversation"""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Champs pour pièces jointes optionnelles
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    
    def __str__(self):
        return f"Message de {self.sender.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        ordering = ['created_at']

class MessageRead(models.Model):
    """Modèle pour suivre quels messages ont été lus par quels utilisateurs"""
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')