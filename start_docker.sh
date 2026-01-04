#!/bin/bash
set -e

echo "🚀 Starting app..."

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --settings=config.settings_production --noinput

# Start Server
echo "🌐 Starting Gunicorn..."
exec gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --access-logfile - --error-logfile -
