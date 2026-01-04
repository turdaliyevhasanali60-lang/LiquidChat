"""
Production settings for LiquidChat.
Import base settings and override for production deployment.
"""

from .settings import *
import os

# Security Settings
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable must be set in production")

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    # Fallback to a broader match if no specific host is provided
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']
else:
    # Ensure standard hosts are always included
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '.onrender.com']

# HTTPS/SSL Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.pythonanywhere.com'
]

# Database - Use environment variables with SQLite fallback
if os.environ.get('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    # Use SQLite if no Postgres is provided (Free tier friendly)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Redis/Channels
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'liquidchat.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# CORS - Restrict in production
# CORS - Restrict in production
CORS_ALLOWED_ORIGINS = [url for url in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if url]
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = ['https://liquidchat-s3bl.onrender.com']
CORS_ALLOW_CREDENTIALS = True
