# accounts/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!'
        }

    def test_user_registration(self):
        """Test qu'un utilisateur peut s'inscrire avec des données valides"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_password_mismatch(self):
        """Test qu'une erreur est retournée si les mots de passe ne correspondent pas"""
        data = self.user_data.copy()
        data['password2'] = 'MismatchPass123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.token_url = reverse('token_obtain_pair')
        self.profile_url = reverse('user-profile')

    def test_user_login(self):
        """Test qu'un utilisateur peut se connecter et obtenir un token"""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.token_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_profile_access(self):
        """Test que l'accès au profil nécessite une authentification"""
        # Sans authentification
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Avec authentification
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

# conversations/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from conversations.models import Conversation, Message

User = get_user_model()

class ConversationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Création de deux utilisateurs
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!'
        )
        
        # URLs
        self.conversations_url = reverse('conversation-list')
        
        # Authentification
        self.client.force_authenticate(user=self.user1)

    def test_create_conversation(self):
        """Test la création d'une nouvelle conversation"""
        data = {
            'participant_id': self.user2.id,
            'message': 'Hello, this is a test message'
        }
        response = self.client.post(self.conversations_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 1)
        
        # Vérification que le message a été créé
        conversation = Conversation.objects.first()
        self.assertEqual(conversation.messages.count(), 1)
        self.assertEqual(conversation.messages.first().content, 'Hello, this is a test message')
        
        # Vérification des participants
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())

    def test_list_conversations(self):
        """Test que l'utilisateur ne voit que ses propres conversations"""
        # Création d'une conversation pour user1 et user2
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        Message.objects.create(conversation=conversation, sender=self.user1, content='Test')
        
        # Création d'une conversation qui n'inclut pas user1
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='TestPass123!'
        )
        other_conversation = Conversation.objects.create()
        other_conversation.participants.add(self.user2, other_user)
        Message.objects.create(conversation=other_conversation, sender=self.user2, content='Test')
        
        # Vérification que user1 ne voit que sa conversation
        response = self.client.get(self.conversations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], conversation.id)

# matching/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from matching.models import Match, UserPreference

User = get_user_model()

class MatchingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Création des utilisateurs
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!'
        )
        
        # Création des préférences
        UserPreference.objects.create(user=self.user1)
        UserPreference.objects.create(user=self.user2)
        
        # URLs
        self.like_url = reverse('like-user')
        self.matches_url = reverse('match-list')
        
        # Authentification
        self.client.force_authenticate(user=self.user1)

    def test_like_user(self):
        """Test l'action de liker un utilisateur"""
        data = {'user_id': self.user2.id}
        response = self.client.post(self.like_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(self.user2, self.user1.liked_users.all())
        self.assertFalse(response.data['is_match'])  # Pas encore de match
        
        # user2 like user1 en retour
        self.client.force_authenticate(user=self.user2)
        data = {'user_id': self.user1.id}
        response = self.client.post(self.like_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_match'])  # Maintenant un match existe
        
        # Vérification que le match a été créé en base de données
        self.assertEqual(Match.objects.count(), 1)
        match = Match.objects.first()
        
        # Les utilisateurs sont ordonnés par ID dans le modèle Match
        if self.user1.id < self.user2.id:
            self.assertEqual(match.user1, self.user1)
            self.assertEqual(match.user2, self.user2)
        else:
            self.assertEqual(match.user1, self.user2)
            self.assertEqual(match.user2, self.user1)

    def test_list_matches(self):
        """Test que l'utilisateur peut voir ses matchs"""
        # Création d'un match
        self.user1.liked_users.add(self.user2)
        self.user2.liked_users.add(self.user1)
        
        # L'ordre des utilisateurs dépend de leurs IDs
        if self.user1.id < self.user2.id:
            user1, user2 = self.user1, self.user2
        else:
            user1, user2 = self.user2, self.user1
            
        Match.objects.create(user1=user1, user2=user2)
        
        # Vérification que l'utilisateur voit le match
        response = self.client.get(self.matches_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)