# matching/models.py

from django.db import models
from django.conf import settings

class UserPreference(models.Model):
    """Préférences de matching des utilisateurs"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Préférences de recherche
    min_age = models.IntegerField(default=18)
    max_age = models.IntegerField(default=99)
    max_distance = models.IntegerField(default=50)  # en km
    
    # Intérêts et tags (pour matching basé sur les intérêts)
    GENDER_CHOICES = (
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('O', 'Autre'),
        ('A', 'Tous'),
    )
    
    gender_preference = models.CharField(max_length=1, choices=GENDER_CHOICES, default='A')
    
    def __str__(self):
        return f"Préférences de {self.user.username}"

class UserInterest(models.Model):
    """Intérêts des utilisateurs pour le matching"""
    
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class UserInterestRelation(models.Model):
    """Relation entre utilisateurs et intérêts"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interests')
    interest = models.ForeignKey(UserInterest, on_delete=models.CASCADE, related_name='interested_users')
    
    class Meta:
        unique_together = ('user', 'interest')
    
    def __str__(self):
        return f"{self.user.username} - {self.interest.name}"

class Match(models.Model):
    """Modèle pour enregistrer les matchs entre utilisateurs"""
    
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"Match entre {self.user1.username} et {self.user2.username}"