# LiquidChat

A real-time chat web application built with Django, Django REST Framework, and Django Channels. LiquidChat features a minimal, glass-like user interface with smooth real-time messaging capabilities.

## Features

- **Real-time messaging** using WebSockets via Django Channels
- **Global chat room** for public discussions
- **Private direct messages** between users
- **JWT authentication** for secure access
- **User presence** (online/offline status)
- **Message history** persistence with PostgreSQL
- **Redis** for real-time features and caching

## Technology Stack

### Backend
- Python 3.x
- Django 4.x
- Django REST Framework
- Django Channels (WebSockets)
- PostgreSQL
- Redis
- Daphne (ASGI server)

### Frontend (assumed)
- HTML/CSS/JavaScript or React/Vue
- WebSocket client support
- REST API consumption

## Project Structure

```
liquidchat/
├── config/                 # Django project configuration
│   ├── asgi.py            # ASGI configuration for WebSockets
│   ├── settings.py        # Project settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── apps/
│   ├── authentication/    # User authentication app
│   │   ├── models.py      # Custom User model
│   │   ├── serializers.py # DRF serializers
│   │   ├── views.py       # API views
│   │   └── urls.py        # Authentication URLs
│   └── chat/              # Chat functionality app
│       ├── models.py      # Conversation, Message models
│       ├── consumers.py   # WebSocket consumers
│       ├── routing.py     # WebSocket URL routing
│       ├── views.py       # REST API views
│       └── urls.py        # Chat URLs
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
└── docker-compose.yml     # Docker Compose configuration
```

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   cd liquidchat
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Using Docker

1. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec django python manage.py migrate
   ```

3. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup/` | Register new user |
| POST | `/api/auth/login/` | Login and get tokens |
| POST | `/api/auth/logout/` | Logout and blacklist token |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET | `/api/auth/users/` | List/search users |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/conversations/` | List user's conversations |
| POST | `/api/chat/conversations/create/` | Create/get conversation |
| GET | `/api/chat/conversations/<id>/` | Get conversation details |
| GET | `/api/chat/conversations/<id>/messages/` | Get message history |
| POST | `/api/chat/conversations/<id>/read/` | Mark messages as read |
| GET | `/api/chat/conversations/user/<user_id>/` | Get/create conversation |
| GET | `/api/chat/global/messages/` | Get global message history |

## WebSocket Endpoints

### Global Chat
```
ws://localhost:8000/ws/chat/global/?token=<jwt_access_token>
```

### Private Chat
```
ws://localhost:8000/ws/chat/private/?token=<jwt_access_token>
```

### WebSocket Events

#### Client to Server

**Send Global Message**
```json
{
  "type": "send_global_message",
  "content": "Hello world"
}
```

**Send Private Message**
```json
{
  "type": "send_private_message",
  "conversation_id": "uuid",
  "content": "Hello!"
}
```

#### Server to Client

**Global Message**
```json
{
  "type": "global_message",
  "message": {
    "id": 1,
    "sender": {"id": "uuid", "username": "alice"},
    "content": "Hello world",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Private Message**
```json
{
  "type": "private_message",
  "message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "sender": {"id": "uuid", "username": "bob"},
    "content": "Hi there!",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**User Presence**
```json
{
  "type": "user_presence",
  "user_id": "uuid",
  "username": "alice",
  "status": "online"  // or "offline"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Enable debug mode | True |
| DJANGO_SECRET_KEY | Secret key for Django | (required) |
| DB_NAME | PostgreSQL database name | liquidchat |
| DB_USER | PostgreSQL user | liquidchat |
| DB_PASSWORD | PostgreSQL password | (required) |
| DB_HOST | PostgreSQL host | localhost |
| DB_PORT | PostgreSQL port | 5432 |
| REDIS_HOST | Redis host | localhost |
| REDIS_PORT | Redis port | 6379 |

### Message Settings

| Setting | Description | Default |
|---------|-------------|---------|
| MESSAGE_MAX_LENGTH | Maximum message length | 2000 |
| MESSAGE_RATE_LIMIT | Messages per second | 1 |
| PRESENCE_HEARTBEAT | Heartbeat interval (seconds) | 30 |
| PRESENCE_EXPIRY | Presence expiry (seconds) | 60 |

## Security Considerations

- All WebSocket connections require JWT authentication
- Message content is sanitized to prevent XSS attacks
- Rate limiting is applied to prevent spam
- Passwords are hashed using Django's default hasher
- Use HTTPS and WSS in production

## License

MIT License
