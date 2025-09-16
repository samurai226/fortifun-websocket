# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Modèle utilisateur personnalisé avec des champs supplémentaires pour le matching"""
    
    # Champ pour lier avec Appwrite
    appwrite_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Champs de base pour le profil
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Champs pour le matching
    location = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Champs de profil
    GENDER_CHOICES = (
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('O', 'Autre'),
        ('A', 'Préfère ne pas dire'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Préférences
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Relations
    liked_users = models.ManyToManyField('self', symmetrical=False, related_name='liked_by', blank=True)
    blocked_users = models.ManyToManyField('self', symmetrical=False, related_name='blocked_by', blank=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.username
    
    @property
    def matches(self):
        """Retourne les utilisateurs avec lesquels il y a un match (like mutuel)"""
        return self.liked_users.filter(liked_users=self)
    
    def get_appwrite_id(self):
        """Retourne l'ID Appwrite de l'utilisateur"""
        return self.appwrite_user_id
    
    def is_appwrite_user(self):
        """Vérifie si l'utilisateur est lié à Appwrite"""
        return bool(self.appwrite_user_id)