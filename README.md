# 🚀 FortiFun HTTP API Server

A Django REST API server for the FortiFun dating app, providing authentication, user management, and data services.

## 🌟 Features

- **RESTful HTTP API**
- **JWT Authentication**
- **User Management**
- **Profile Management**
- **File Upload (S3)**
- **Database Operations**
- **Health Monitoring**

## 🔧 API Endpoints

- **Authentication**: `https://your-app.onrender.com/api/v1/accounts/auth/`
- **User Management**: `https://your-app.onrender.com/api/v1/accounts/users/`
- **File Upload**: `https://your-app.onrender.com/api/v1/accounts/upload/`

## 🚀 Deployment

This server is optimized for deployment on Render with the following configuration:

### Build Command:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

### Start Command:
```bash
python manage.py runserver 0.0.0.0:$PORT
```

### Environment Variables:
- `SECRET_KEY`: Django secret key
- `DEBUG`: False
- `ALLOWED_HOSTS`: *.onrender.com
- `DATABASE_URL`: Auto-provided by Render
- `REDIS_URL`: Auto-provided by Render

## 📱 Flutter Integration

Update your Flutter app's `DjangoService` with the deployed URL:

```dart
class DjangoService {
  static const String baseUrl = 'https://your-app.onrender.com';
  static const String wsUrl = 'wss://your-app.onrender.com/ws/chat/';
}
```

## 🧪 Testing

Test WebSocket connection in browser console:

```javascript
const ws = new WebSocket('wss://your-app.onrender.com/ws/chat/?token=YOUR_JWT_TOKEN');
ws.onopen = () => console.log('✅ Connected!');
ws.onmessage = (event) => console.log('📥 Message:', event.data);
```

## 📊 API Endpoints

- `POST /api/v1/accounts/auth/register` - User registration
- `POST /api/v1/accounts/auth/login` - User login
- `POST /api/v1/accounts/auth/refresh` - Token refresh
- `GET /api/v1/accounts/users/me` - Get current user
- `POST /api/v1/accounts/auth/logout` - Logout

## 🔒 Security

- JWT-based authentication
- CORS configured for Flutter app
- WebSocket authentication middleware
- Secure token handling

Built with ❤️ for FortiFun