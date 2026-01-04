#!/bin/bash
set -e

echo "🚀 Starting app..."

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --settings=config.settings_production --noinput

# Create Superuser if not exists
echo "👤 Checking for superuser..."
python << END
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_production")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
if not User.objects.filter(username=username).exists():
    print(f"Creating superuser: {username}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print(f"Superuser {username} already exists.")
END

# Start Server
echo "🌐 Starting Gunicorn..."
exec gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --access-logfile - --error-logfile -
