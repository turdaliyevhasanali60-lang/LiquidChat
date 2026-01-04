# LiquidChat Deployment Guide

## 🚀 Production Deployment

This guide covers deploying LiquidChat to production using Docker Compose with Nginx.

### Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificate (Let's Encrypt recommended)

### Quick Start

1. **Configure Environment**
   ```bash
   cp .env.production .env
   # Edit .env with your production values
   ```

2. **Update Configuration**
   - Set `DJANGO_SECRET_KEY` to a secure random value
   - Configure `ALLOWED_HOSTS` with your domain
   - Set database credentials
   - Configure Redis connection

3. **Update Nginx Configuration**
   ```bash
   # Edit nginx.conf
   # Replace 'yourdomain.com' with your actual domain
   ```

4. **Build and Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

5. **Run Migrations**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

7. **Collect Static Files**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   ```

### SSL/TLS Setup

For Let's Encrypt SSL certificates:

```bash
# Install certbot
docker-compose -f docker-compose.prod.yml run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com
```

### Environment Variables

Required environment variables in `.env`:

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=liquidchat
DB_USER=liquidchat
DB_PASSWORD=secure-password
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Manual Deployment (Without Docker)

1. **Install Dependencies**
   ```bash
   ./deploy.sh
   ```

2. **Configure Production Settings**
   ```bash
   export DJANGO_SETTINGS_MODULE=config.settings_production
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn config.asgi:application \
     -k uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000 \
     --workers 4 \
     --access-logfile - \
     --error-logfile -
   ```

### Monitoring

- Application logs: `docker-compose -f docker-compose.prod.yml logs -f web`
- Database logs: `docker-compose -f docker-compose.prod.yml logs -f db`
- Redis logs: `docker-compose -f docker-compose.prod.yml logs -f redis`

### Backup

```bash
# Database backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U liquidchat liquidchat > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T db psql -U liquidchat liquidchat < backup.sql
```

### Security Checklist

- ✅ DEBUG=False in production
- ✅ Strong SECRET_KEY configured
- ✅ HTTPS/SSL enabled
- ✅ ALLOWED_HOSTS restricted
- ✅ Database password secured
- ✅ CORS origins restricted
- ✅ Security headers enabled
- ✅ Static files served via WhiteNoise/Nginx

### Performance Optimization

1. **Database Connection Pooling**: Already configured with `CONN_MAX_AGE=600`
2. **Redis Caching**: Configured for sessions and presence
3. **Static File Compression**: WhiteNoise handles compression
4. **WebSocket Scaling**: Use multiple Gunicorn workers

### Troubleshooting

**WebSocket Connection Issues:**
- Ensure Nginx is configured for WebSocket upgrade
- Check firewall allows WebSocket connections
- Verify Redis is accessible

**Static Files Not Loading:**
```bash
python manage.py collectstatic --noinput
```

**Database Connection Errors:**
- Verify database credentials in `.env`
- Check database service is running
- Ensure migrations are applied

## 📊 Health Checks

Access health endpoints:
- Admin: `https://yourdomain.com/admin/`
- API: `https://yourdomain.com/api/auth/login/`

## 🔄 Updates

To update the application:

```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```
