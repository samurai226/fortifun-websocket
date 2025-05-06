# API Chat & Matching - Django

Une API backend pour une application de chat avec fonctionnalités de matching, construite avec Django et Django REST Framework.

## Fonctionnalités

- **Authentification** : JWT (JSON Web Token)
- **Gestion des utilisateurs** : Inscription, connexion, gestion de profils
- **Conversations** : Messagerie en temps réel (prête pour l'intégration avec WebSockets)
- **Matching** : Système de likes, matches, et préférences utilisateur
- **Blocage d'utilisateurs** : Possibilité de bloquer et débloquer des utilisateurs

## Configuration du projet

### Prérequis

- Python 3.8+ 
- pip (gestionnaire de packages Python)

### Installation

1. Cloner le dépôt
```bash
git clone <repository-url>
cd chat_api
```

2. Créer un environnement virtuel
```bash
python -m venv venv
```

3. Activer l'environnement virtuel
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

4. Installer les dépendances
```bash
pip install -r requirements.txt
```

5. Configurer les variables d'environnement (ou modifier settings.py)
```bash
# Exemple avec un fichier .env
SECRET_KEY=your_secret_key
DEBUG=True
```

6. Appliquer les migrations
```bash
python manage.py makemigrations accounts conversations matching
python manage.py migrate
```

7. Créer un superutilisateur (facultatif)
```bash
python manage.py createsuperuser
```

8. Lancer le serveur de développement
```bash
python manage.py runserver
```

## Structure de l'API

L'API est structurée en trois applications principales :

1. **accounts** : Gestion des utilisateurs et de l'authentification
2. **conversations** : Gestion des conversations et des messages
3. **matching** : Système de matching et préférences utilisateur

### Points d'entrée principaux

#### Authentification
- `POST /api/token/` : Obtenir un token JWT
- `POST /api/token/refresh/` : Rafraîchir un token JWT
- `POST /api/v1/auth/register/` : Inscription d'un nouvel utilisateur
- `POST /api/v1/auth/logout/` : Déconnexion (invalidation du token)

#### Utilisateurs
- `GET/PUT /api/v1/auth/profile/` : Consulter/modifier son profil
- `GET /api/v1/auth/users/<id>/` : Consulter le profil d'un utilisateur
- `PUT /api/v1/auth/change-password/` : Changer son mot de passe
- `POST /api/v1/auth/update-status/` : Mettre à jour son statut en ligne

#### Conversations
- `GET /api/v1/conversations/` : Liste des conversations
- `POST /api/v1/conversations/` : Créer une nouvelle conversation
- `GET /api/v1/conversations/<id>/` : Détails d'une conversation
- `DELETE /api/v1/conversations/<id>/leave/` : Quitter une conversation

#### Messages
- `GET /api/v1/conversations/<id>/messages/` : Liste des messages d'une conversation
- `POST /api/v1/conversations/<id>/messages/` : Envoyer un nouveau message
- `POST /api/v1/conversations/<id>/messages/<id>/mark_read/` : Marquer un message comme lu

#### Matching
- `GET/PUT /api/v1/matching/preferences/` : Consulter/modifier ses préférences de matching
- `GET /api/v1/matching/potential-matches/` : Liste des matches potentiels
- `GET /api/v1/matches/` : Liste des matches
- `POST /api/v1/matching/like/` : Liker un utilisateur
- `POST /api/v1/matching/unlike/` : Retirer un like
- `POST /api/v1/matching/block/` : Bloquer un utilisateur
- `POST /api/v1/matching/unblock/` : Débloquer un utilisateur

## Extensions possibles

- Intégration de WebSockets pour les messages en temps réel
- Système de notifications
- Algorithme de matching avancé
- Modération des messages
- Gestion des médias (images, vidéos, etc.)

## Sécurité

- Tous les points d'entrée (sauf inscription et login) nécessitent un token JWT valide
- Les mots de passe sont hachés avec l'algorithme par défaut de Django
- Protection CSRF activée
- En production, configurer CORS et HTTPS

## Licence

[Votre licence]
