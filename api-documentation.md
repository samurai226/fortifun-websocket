# Documentation API Chat & Matching

Cette documentation décrit en détail l'API de chat et matching développée avec Django et Django REST Framework.

## Table des matières

1. [Authentification](#authentification)
2. [Utilisateurs](#utilisateurs)
3. [Conversations](#conversations)
4. [Messages](#messages)
5. [Matching](#matching)
6. [Codes d'erreur](#codes-derreur)

## Authentification

L'API utilise l'authentification par JWT (JSON Web Token). Pour accéder aux endpoints protégés, un token valide doit être inclus dans les en-têtes des requêtes.

### Obtenir un token

```
POST /api/token/
```

Paramètres (body JSON) :
- `username` (obligatoire) : Nom d'utilisateur
- `password` (obligatoire) : Mot de passe

Réponse réussie (200 OK) :
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

### Rafraîchir un token

```
POST /api/token/refresh/
```

Paramètres (body JSON) :
- `refresh` (obligatoire) : Token de rafraîchissement obtenu précédemment

Réponse réussie (200 OK) :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

### Déconnexion (invalidation du token)

```
POST /api/v1/auth/logout/
```

Paramètres (body JSON) :
- `refresh` (obligatoire) : Token de rafraîchissement à invalider

Réponse réussie (200 OK) :
```json
{
  "detail": "Déconnexion réussie"
}
```

## Utilisateurs

### Inscription

```
POST /api/v1/auth/register/
```

Paramètres (body JSON) :
- `username` (obligatoire) : Nom d'utilisateur unique
- `email` (obligatoire) : Adresse e-mail
- `password` (obligatoire) : Mot de passe
- `password2` (obligatoire) : Confirmation du mot de passe
- `first_name` (optionnel) : Prénom
- `last_name` (optionnel) : Nom de famille

Réponse réussie (201 Created) :
```json
{
  "username": "example_user",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Profil utilisateur

```
GET /api/v1/auth/profile/
```

Réponse réussie (200 OK) :
```json
{
  "id": 1,
  "username": "example_user",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "profile_picture": "http://example.com/media/profile_pictures/picture.jpg",
  "bio": "À propos de moi...",
  "date_of_birth": "1990-01-01",
  "phone_number": "+33612345678",
  "location": "Paris, France",
  "is_online": true,
  "last_activity": "2023-05-15T14:30:45Z",
  "interests": [
    {"id": 1, "name": "sports"},
    {"id": 2, "name": "musique"}
  ],
  "preferences": {
    "min_age": 18,
    "max_age": 40,
    "max_distance": 50,
    "gender_preference": "A"
  }
}
```

### Mise à jour du profil

```
PUT /api/v1/auth/profile/
```

Paramètres (body JSON ou form-data pour les fichiers) :
- `username` (optionnel) : Nouveau nom d'utilisateur
- `email` (optionnel) : Nouvelle adresse e-mail
- `first_name` (optionnel) : Prénom
- `last_name` (optionnel) : Nom de famille
- `profile_picture` (optionnel) : Photo de profil (fichier)
- `bio` (optionnel) : Biographie
- `date_of_birth` (optionnel) : Date de naissance (format YYYY-MM-DD)
- `phone_number` (optionnel) : Numéro de téléphone
- `location` (optionnel) : Localisation (texte)
- `latitude` (optionnel) : Latitude
- `longitude` (optionnel) : Longitude
- `interests` (optionnel) : Liste des intérêts ["sport", "musique", "cinéma", ...]

Réponse réussie (200 OK) : Même format que pour GET /api/v1/auth/profile/

### Consulter un profil utilisateur

```
GET /api/v1/auth/users/{id}/
```

Réponse réussie (200 OK) : Même format que pour GET /api/v1/auth/profile/

### Changer de mot de passe

```
PUT /api/v1/auth/change-password/
```

Paramètres (body JSON) :
- `old_password` (obligatoire) : Mot de passe actuel
- `new_password` (obligatoire) : Nouveau mot de passe
- `new_password2` (obligatoire) : Confirmation du nouveau mot de passe

Réponse réussie (200 OK) :
```json
{
  "detail": "Mot de passe changé avec succès"
}
```

### Mettre à jour le statut en ligne

```
POST /api/v1/auth/update-status/
```

Réponse réussie (200 OK) :
```json
{
  "detail": "Statut en ligne mis à jour"
}
```

## Conversations

### Liste des conversations

```
GET /api/v1/conversations/
```

Réponse réussie (200 OK) :
```json
[
  {
    "id": 1,
    "participants": [
      {
        "id": 1,
        "username": "example_user",
        "profile_picture": "http://example.com/media/profile_pictures/picture.jpg"
      },
      {
        "id": 2,
        "username": "other_user",
        "profile_picture": "http://example.com/media/profile_pictures/other.jpg"
      }
    ],
    "created_at": "2023-05-15T14:00:00Z",
    "updated_at": "2023-05-15T14:30:45Z",
    "is_active": true,
    "last_message": {
      "id": 10,
      "conversation": 1,
      "sender": {
        "id": 2,
        "username": "other_user",
        "profile_picture": "http://example.com/media/profile_pictures/other.jpg"
      },
      "content": "Bonjour, comment ça va ?",
      "created_at": "2023-05-15T14:30:45Z",
      "is_read": false,
      "attachment": null,
      "is_read_by_recipient": false
    },
    "unread_count": 1
  }
]
```

### Créer une nouvelle conversation

```
POST /api/v1/conversations/
```

Paramètres (body JSON) :
- `participant_id` (obligatoire) : ID de l'utilisateur avec qui commencer la conversation
- `message` (obligatoire) : Premier message de la conversation

Réponse réussie (201 Created) : Mêmes détails qu'une conversation individuelle (comme ci-dessus)

### Détails d'une conversation

```
GET /api/v1/conversations/{id}/
```

Réponse réussie (200 OK) : Mêmes détails qu'une conversation individuelle (comme ci-dessus)

### Quitter une conversation

```
DELETE /api/v1/conversations/{id}/leave/
```

Réponse réussie (200 OK) :
```json
{
  "detail": "Conversation supprimée avec succès"
}
```

## Messages

### Liste des messages d'une conversation

```
GET /api/v1/conversations/{conversation_id}/messages/
```

Réponse réussie (200 OK) :
```json
[
  {
    "id": 1,
    "conversation": 1,
    "sender": {
      "id": 1,
      "username": "example_user",
      "profile_picture": "http://example.com/media/profile_pictures/picture.jpg"
    },
    "content": "Salut !",
    "created_at": "2023-05-15T14:00:00Z",
    "is_read": true,
    "attachment": null,
    "is_read_by_recipient": true
  },
  {
    "id": 2,
    "conversation": 1,
    "sender": {
      "id": 2,
      "username": "other_user",
      "profile_picture": "http://example.com/media/profile_pictures/other.jpg"
    },
    "content": "Bonjour, comment ça va ?",
    "created_at": "2023-05-15T14:01:00Z",
    "is_read": false,
    "attachment": null,
    "is_read_by_recipient": false
  }
]
```

### Envoyer un message

```
POST /api/v1/conversations/{conversation_id}/messages/
```

Paramètres (body JSON ou form-data pour les pièces jointes) :
- `content` (obligatoire) : Contenu du message
- `attachment` (optionnel) : Pièce jointe (fichier)

Réponse réussie (201 Created) : Détails du message créé (comme ci-dessus)

### Marquer un message comme lu

```
POST /api/v1/conversations/{conversation_id}/messages/{message_id}/mark_read/
```

Réponse réussie (200 OK) :
```json
{
  "detail": "Message marqué comme lu"
}
```

## Matching

### Préférences de matching

#### Consulter ses préférences

```
GET /api/v1/matching/preferences/
```

Réponse réussie (200 OK) :
```json
{
  "min_age": 18,
  "max_age": 40,
  "max_distance": 50,
  "gender_preference": "A"
}
```

#### Mettre à jour ses préférences

```
PUT /api/v1/matching/preferences/
```

Paramètres (body JSON) :
- `min_age` (optionnel) : Âge minimum pour les matchs (par défaut: 18)
- `max_age` (optionnel) : Âge maximum pour les matchs (par défaut: 99)
- `max_distance` (optionnel) : Distance maximale en km (par défaut: 50)
- `gender_preference` (optionnel) : Préférence de genre ("M", "F", "O", "A")

Réponse réussie (200 OK) : Mêmes détails que GET /api/v1/matching/preferences/

### Utilisateurs potentiels pour le matching

```
GET /api/v1/matching/potential-matches/
```

Réponse réussie (200 OK) :
```json
[
  {
    "id": 2,
    "username": "potential_match",
    "first_name": "Jane",
    "last_name": "Smith",
    "profile_picture": "http://example.com/media/profile_pictures/jane.jpg",
    "bio": "Biographie de Jane",
    "location": "Lyon, France",
    "is_online": true,
    "last_activity": "2023-05-15T14:30:45Z",
    "interests": ["voyage", "cuisine", "lecture"],
    "age": 28,
    "distance": 15.3
  }
]
```

### Liste des matchs

```
GET /api/v1/matches/
```

Réponse réussie (200 OK) :
```json
[
  {
    "id": 1,
    "created_at": "2023-05-14T10:00:00Z",
    "is_active": true,
    "matched_user": {
      "id": 3,
      "username": "match_user",
      "first_name": "Robert",
      "last_name": "Johnson",
      "profile_picture": "http://example.com/media/profile_pictures/robert.jpg",
      "bio": "Biographie de Robert",
      "location": "Paris, France",
      "is_online": false,
      "last_activity": "2023-05-14T18:45:30Z",
      "interests": ["sport", "technologie", "voyages"],
      "age": 32,
      "distance": 5.7
    }
  }
]
```

### Liker un utilisateur

```
POST /api/v1/matching/like/
```

Paramètres (body JSON) :
- `user_id` (obligatoire) : ID de l'utilisateur à liker

Réponse réussie (201 Created) :
```json
{
  "detail": "Like enregistré avec succès",
  "is_match": true,  // ou false si pas de match
  "match": {         // présent uniquement si is_match est true
    "id": 1,
    "created_at": "2023-05-15T15:00:00Z",
    "is_active": true,
    "matched_user": {
      "id": 4,
      "username": "new_match",
      // ... autres détails de l'utilisateur
    }
  }
}
```

### Annuler un like

```
POST /api/v1/matching/unlike/
```

Paramètres (body JSON) :
- `user_id` (obligatoire) : ID de l'utilisateur dont on veut retirer le like

Réponse réussie (200 OK) :
```json
{
  "detail": "Like annulé avec succès"
}
```

### Bloquer un utilisateur

```
POST /api/v1/matching/block/
```

Paramètres (body JSON) :
- `user_id` (obligatoire) : ID de l'utilisateur à bloquer

Réponse réussie (200 OK) :
```json
{
  "detail": "Utilisateur bloqué avec succès"
}
```

### Débloquer un utilisateur

```
POST /api/v1/matching/unblock/
```

Paramètres (body JSON) :
- `user_id` (obligatoire) : ID de l'utilisateur à débloquer

Réponse réussie (200 OK) :
```json
{
  "detail": "Utilisateur débloqué avec succès"
}
```

## Codes d'erreur

L'API utilise les codes d'erreur HTTP standard avec des messages d'erreur spécifiques.

### Erreurs communes

- `400 Bad Request` : Requête invalide (données manquantes ou incorrectes)
- `401 Unauthorized` : Authentification requise
- `403 Forbidden` : Accès refusé
- `404 Not Found` : Ressource introuvable
- `405 Method Not Allowed` : Méthode HTTP non autorisée
- `500 Internal Server Error` : Erreur interne du serveur

### Exemples d'erreurs spécifiques

#### Erreur d'authentification

```json
{
  "detail": "Identifiants d'authentification non fournis."
}
```

#### Erreur de validation

```json
{
  "password": [
    "Les mots de passe ne correspondent pas."
  ],
  "email": [
    "Un utilisateur avec cette adresse e-mail existe déjà."
  ]
}
```

#### Erreur d'accès

```json
{
  "detail": "Vous n'avez pas la permission d'effectuer cette action."
}
```

#### Ressource introuvable

```json
{
  "detail": "Pas trouvé."
}
```
