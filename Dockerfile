FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings_production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn uvicorn[standard] whitenoise django-redis

# Copy project
COPY . /app/

# Create logs directory
RUN mkdir -p /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings_production || true

# Create non-root user
RUN useradd -m -u 1000 liquidchat && \
    chown -R liquidchat:liquidchat /app
# Copy start script using a simpler COPY command since permissions are sometimes lost
COPY start_docker.sh /app/start_docker.sh
USER root
RUN chmod +x /app/start_docker.sh
USER liquidchat

# Run start script
CMD ["/app/start_docker.sh"]
