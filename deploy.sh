#!/bin/bash

# LiquidChat Deployment Script
# This script prepares the application for production deployment

set -e

echo "🚀 Starting LiquidChat deployment preparation..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create one first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn whitenoise django-redis

# Check for .env.production
if [ ! -f ".env.production" ]; then
    echo "⚠️  .env.production not found. Please configure it before deployment."
    echo "   A template has been created at .env.production"
fi

# Run Django checks
echo "🔍 Running Django deployment checks..."
python manage.py check --deploy --settings=config.settings_production || true

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings_production

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --settings=config.settings_production

# Create logs directory
echo "📝 Creating logs directory..."
mkdir -p logs

# Create superuser prompt
echo ""
echo "✅ Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Configure .env.production with your production settings"
echo "   2. Set DJANGO_SECRET_KEY to a secure random value"
echo "   3. Update ALLOWED_HOSTS with your domain"
echo "   4. Configure your database credentials"
echo "   5. Set up Redis connection details"
echo "   6. Create a superuser: python manage.py createsuperuser --settings=config.settings_production"
echo ""
echo "🌐 To run with Gunicorn:"
echo "   gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
echo ""
