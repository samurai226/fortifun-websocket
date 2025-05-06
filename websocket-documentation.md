# Documentation WebSockets pour l'API Chat & Matching

Cette documentation explique comment utiliser les WebSockets pour les communications en temps réel dans l'API Chat & Matching Django.

## Table des matières

1. [Introduction aux WebSockets](#introduction-aux-websockets)
2. [Configuration requise](#configuration-requise)
3. [Points de terminaison WebSockets](#points-de-terminaison-websockets)
4. [Authentification](#authentification)
5. [Messages et formats de données](#messages-et-formats-de-données)
6. [Exemples d'utilisation](#exemples-dutilisation)
7. [Gestion des erreurs](#gestion-des-erreurs)
8. [Bonnes pratiques](#bonnes-pratiques)

## Introduction aux WebSockets

Les WebSockets permettent une communication bidirectionnelle en temps réel entre le client et le serveur. Dans notre API, ils sont utilisés pour :

- Envoi et réception de messages instantanés
- Notifications en temps réel (nouveaux matchs, likes, etc.)
- Statuts de présence des utilisateurs (en ligne/hors ligne)
- Indicateurs de frappe (utilisateur en train d'écrire)
- Accusés de lecture des messages

## Configuration requise

Pour utiliser les WebSockets, vous avez besoin de :

- Redis (comme couche de communication entre les différentes instances du serveur)
- Les bibliothèques Python : `channels`, `daphne`, `channels-redis`

Installation :

```bash
pip install channels daphne channels-redis redis
```

Configuration de Redis :
- En local : Redis doit être en cours d'exécution sur localhost:6379 (port par défaut)
- En production : Configurez l'hôte et le port dans `settings.py`

## Points de terminaison WebSockets

L'API expose deux points de terminaison WebSockets principaux :

1. **Conversations** : pour les messages en temps réel
   ```
   ws://<host>/ws/conversations/<conversation_id>/?token=<jwt_token>
   ```

2. **Notifications** : pour les notifications générales
   ```
   ws://<host>/ws/notifications/?token=<jwt_token>
   ```

En production, utilisez `wss://` au lieu de `ws://` pour une connexion sécurisée.

## Authentification

L'authentification se fait via le token JWT :

1. Obtenez un token JWT via l'endpoint REST API (`/api/token/`)
2. Passez le token dans les paramètres de requête de l'URL WebSocket :
   ```
   ws://<host>/ws/conversations/123/?token=eyJ0eXAiOiJKV1QiLCJhbGc...
   ```

## Messages et formats de données

### Connexion aux conversations

Une fois connecté, vous pouvez envoyer et recevoir des messages selon les formats suivants :

### Envoyer des messages

Pour envoyer un message dans une conversation :

```json
{
  "type": "message",
  "content": "Bonjour, comment ça va ?"
}
```

### Simuler la frappe

Pour indiquer que l'utilisateur est en train d'écrire :

```json
{
  "type": "typing",
  "is_typing": true
}
```

Pour indiquer que l'utilisateur a arrêté d'écrire :

```json
{
  "type": "typing",
  "is_typing": false
}
```

### Marquer un message comme lu

Pour envoyer un accusé de lecture :

```json
{
  "type": "read_receipt",
  "message_id": 123
}
```

### Réception de messages

Voici les différents types de messages que vous pouvez recevoir :

#### Nouveau message

```json
{
  "type": "message",
  "message": {
    "id": 456,
    "sender_id": 789,
    "sender_username": "sophie",
    "sender_profile_picture": "http://example.com/media/profile_pictures/sophie.jpg",
    "content": "Salut, ça va ?",
    "created_at": "2023-05-15T14:30:45Z",
    "is_read": false,
    "attachment": null
  }
}
```

#### Accusé de lecture

```json
{
  "type": "read_receipt",
  "message_id": 456,
  "user_id": 123,
  "username": "robert",
  "timestamp": "2023-05-15T14:32:10Z"
}
```

#### Notification de frappe

```json
{
  "type": "typing",
  "user_id": 789,
  "username": "sophie",
  "is_typing": true
}
```

#### Statut utilisateur

```json
{
  "type": "status",
  "user_id": 789,
  "username": "sophie",
  "status": "online",
  "timestamp": "2023-05-15T14:29:30Z"
}
```

### Connexion aux notifications

Le WebSocket de notifications envoie des données dans le format suivant :

#### Notification de nouveau message

```json
{
  "type": "notification",
  "notification": {
    "type": "new_message",
    "timestamp": "2023-05-15T14:30:45Z",
    "message": {
      "id": 456,
      "conversation_id": 123,
      "sender": {
        "id": 789,
        "username": "sophie",
        "profile_picture": "http://example.com/media/profile_pictures/sophie.jpg"
      },
      "content": "Salut, ça va ?",
      "created_at": "2023-05-15T14:30:45Z"
    }
  }
}
```

#### Notification de nouveau match

```json
{
  "type": "notification",
  "notification": {
    "type": "new_match",
    "timestamp": "2023-05-15T14:35:12Z",
    "match": {
      "id": 789,
      "user": {
        "id": 456,
        "username": "robert",
        "profile_picture": "http://example.com/media/profile_pictures/robert.jpg"
      },
      "created_at": "2023-05-15T14:35:12Z"
    }
  }
}
```

#### Notification de nouveau like

```json
{
  "type": "notification",
  "notification": {
    "type": "new_like",
    "timestamp": "2023-05-15T14:40:22Z",
    "liker": {
      "id": 123,
      "username": "thomas",
      "profile_picture": "http://example.com/media/profile_pictures/thomas.jpg"
    }
  }
}
```

## Exemples d'utilisation

### Connexion à une conversation avec JavaScript

```javascript
// Obtenir le token JWT (via l'API REST)
const token = "eyJ0eXAiOiJKV1QiLCJhbGc...";
const conversationId = 123;

// Créer la connexion WebSocket
const socket = new WebSocket(`ws://example.com/ws/conversations/${conversationId}/?token=${token}`);

// Gérer les événements WebSocket
socket.onopen = (event) => {
  console.log("Connexion WebSocket établie");
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Traiter les différents types de messages
  switch (data.type) {
    case "message":
      console.log(`Nouveau message de ${data.message.sender_username}: ${data.message.content}`);
      break;
    case "typing":
      if (data.is_typing) {
        console.log(`${data.username} est en train d'écrire...`);
      } else {
        console.log(`${data.username} a arrêté d'écrire`);
      }
      break;
    case "read_receipt":
      console.log(`Message ${data.message_id} lu par ${data.username}`);
      break;
    case "status":
      console.log(`${data.username} est ${data.status}`);
      break;
    default:
      console.log("Message inconnu", data);
  }
};

socket.onclose = (event) => {
  console.log(`Connexion fermée: ${event.code} ${event.reason}`);
};

socket.onerror = (error) => {
  console.error("Erreur WebSocket:", error);
};

// Envoyer un message
function sendMessage(content) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: "message",
      content: content
    }));
  } else {
    console.error("WebSocket n'est pas connecté");
  }
}

// Indiquer que l'utilisateur est en train d'écrire
function sendTypingStatus(isTyping) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: "typing",
      is_typing: isTyping
    }));
  }
}

// Marquer un message comme lu
function markMessageAsRead(messageId) {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: "read_receipt",
      message_id: messageId
    }));
  }
}
```

### Connexion aux notifications avec JavaScript

```javascript
// Obtenir le token JWT (via l'API REST)
const token = "eyJ0eXAiOiJKV1QiLCJhbGc...";

// Créer la connexion WebSocket pour les notifications
const notificationSocket = new WebSocket(`ws://example.com/ws/notifications/?token=${token}`);

notificationSocket.onopen = (event) => {
  console.log("Connexion aux notifications établie");
};

notificationSocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "notification") {
    const notification = data.notification;
    
    // Traiter les différents types de notifications
    switch (notification.type) {
      case "new_message":
        console.log(`Nouveau message de ${notification.message.sender.username} dans la conversation ${notification.message.conversation_id}`);
        break;
      case "new_match":
        console.log(`Nouveau match avec ${notification.match.user.username}`);
        break;
      case "new_like":
        console.log(`${notification.liker.username} vous a liké`);
        break;
      default:
        console.log("Notification inconnue", notification);
    }
  }
};
```

## Gestion des erreurs

### Codes d'erreur WebSocket

Les WebSockets peuvent se fermer avec les codes d'erreur suivants :

- `1000` : Fermeture normale
- `1001` : L'application se termine ou l'hôte se déconnecte
- `1006` : Connexion fermée anormalement (erreur réseau)
- `1008` : Politique violée (erreur d'authentification)
- `1011` : Erreur inattendue côté serveur
- `4000` : Utilisateur non authentifié
- `4001` : Accès refusé (pas un participant de la conversation)
- `4002` : Erreur d'authentification du token JWT
- `4003` : Format de message invalide

### Stratégie de reconnexion

Pour une expérience utilisateur optimale, implémentez une stratégie de reconnexion en cas de déconnexion :

```javascript
function connect() {
  // ... code de connexion WebSocket

  socket.onclose = (event) => {
    console.log(`Connexion fermée: ${event.code} ${event.reason}`);
    
    // Ne pas tenter de se reconnecter en cas d'erreur d'authentification
    if (event.code === 1008 || event.code === 4000 || event.code === 4001 || event.code === 4002) {
      console.error("Erreur d'authentification, reconnexion impossible");
      return;
    }
    
    // Tenter de se reconnecter avec un délai exponentiel
    setTimeout(() => {
      console.log("Tentative de reconnexion...");
      connect();
    }, calculateReconnectDelay());
  };
}

// Exemple de fonction pour calculer un délai exponentiel avec jitter
let reconnectAttempt = 0;
function calculateReconnectDelay() {
  const baseDelay = 1000; // 1 seconde
  const maxDelay = 30000; // 30 secondes maximum
  
  // Délai exponentiel: 1s, 2s, 4s, 8s, 16s, etc.
  const exponentialDelay = Math.min(baseDelay * Math.pow(2, reconnectAttempt), maxDelay);
  
  // Ajouter un jitter (±20%) pour éviter les reconnexions simultanées
  const jitter = exponentialDelay * 0.2 * (Math.random() * 2 - 1);
  
  reconnectAttempt++;
  return exponentialDelay + jitter;
}
```

## Bonnes pratiques

### Performances et optimisation

1. **Limitez le nombre de connexions WebSocket** par utilisateur
   - Une connexion pour les conversations actives
   - Une connexion pour les notifications générales

2. **Utilisez une stratégie de reconnexion intelligente**
   - Délai exponentiel pour éviter de surcharger le serveur
   - Jitter pour éviter les reconnexions simultanées
   - Arrêtez les tentatives après un certain nombre d'échecs

3. **Minimisez la taille des payloads**
   - N'envoyez que les données nécessaires
   - Utilisez des IDs courts et significatifs

4. **Gérez correctement la déconnexion**
   - Fermez proprement la connexion lorsque l'utilisateur quitte l'application
   - Mettez à jour le statut utilisateur côté serveur

### Sécurité

1. **Utilisez toujours HTTPS/WSS en production**
   - Les WebSockets en production doivent toujours utiliser WSS (WebSocket Secure)

2. **Validez toutes les données**
   - Ne faites jamais confiance aux données reçues du client sans validation
   - Vérifiez que l'utilisateur a le droit d'accéder à la conversation

3. **Protégez contre les attaques de déni de service**
   - Limitez le nombre de messages par unité de temps
   - Limitez le nombre de connexions par utilisateur

4. **Stockez seulement temporairement les données sensibles**
   - Ne stockez pas en mémoire des informations sensibles plus longtemps que nécessaire

### Intégration avec d'autres systèmes

1. **Intégration avec les notifications push mobiles**
   - Les notifications WebSocket complètent les notifications push
   - Utilisez les WebSockets pour les utilisateurs actifs
   - Utilisez les notifications push pour les utilisateurs inactifs

2. **Synchronisation avec l'API REST**
   - Les WebSockets peuvent accélérer les mises à jour en temps réel
   - L'API REST reste la source de vérité pour toutes les données
   - Utilisez l'API REST pour la récupération initiale des données et les WebSockets pour les mises à jour

## Dépannage

### Problèmes courants et solutions

1. **La connexion échoue immédiatement**
   - Vérifiez que le token JWT est valide
   - Vérifiez que l'URL WebSocket est correcte
   - Vérifiez que l'utilisateur a accès à la ressource (conversation)

2. **La connexion se ferme après quelques secondes**
   - Vérifiez que Redis est en cours d'exécution
   - Vérifiez que le token JWT n'est pas expiré
   - Recherchez des erreurs dans les logs du serveur

3. **Les messages ne sont pas reçus par tous les participants**
   - Vérifiez que tous les utilisateurs sont bien dans le même groupe de canal
   - Vérifiez que Redis fonctionne correctement
   - Assurez-vous que les connexions WebSocket des utilisateurs sont actives

4. **Problèmes de performance**
   - Surveillez l'utilisation mémoire de Redis
   - Réduisez la quantité de données envoyées via WebSockets
   - Utilisez un outil de monitoring comme Prometheus pour surveiller les performances

Pour tout problème persistant, consultez les logs du serveur Django et Redis pour des informations plus détaillées sur les erreurs potentielles.
