# FINESE2 Deployment Guide

This guide covers deploying FINESE2 to various environments.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)

---

## Local Development

### Quick Start
```bash
py main.py --host 0.0.0.0 --port 5000 --debug
```

### With Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
py main.py --host 0.0.0.0 --port 5000 --debug
```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended)

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f web
```

**Stop services:**
```bash
docker-compose down
```

**With volume persistence:**
```bash
docker-compose up -d
# Data persists in Docker volumes
```

### Option 2: Docker Only

**Build image:**
```bash
docker build -t finese2:latest .
```

**Run container:**
```bash
docker run -d \
  --name finese2 \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=sqlite:///instance/finese2.db \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/reports:/app/reports \
  finese2:latest
```

**With Redis:**
```bash
# Start Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start FINESE2 with Redis
docker run -d \
  --name finese2 \
  -p 5000:5000 \
  --link redis:redis \
  -e REDIS_URL=redis://redis:6379/0 \
  -e SECRET_KEY=your-secret-key \
  finese2:latest
```

---

## Production Deployment

### Prerequisites

1. **Set strong secret keys**
2. **Use PostgreSQL instead of SQLite**
3. **Enable HTTPS**
4. **Configure proper logging**
5. **Set up monitoring**

### Environment Variables for Production

Create `.env.production`:
```bash
# Security
SECRET_KEY=use-a-strong-random-key-here
JWT_SECRET_KEY=another-strong-random-key
ENABLE_JWT=true

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/finese2

# Redis
REDIS_URL=redis://redis-host:6379/0

# Application
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=WARNING

# Upload limits
MAX_UPLOAD_SIZE=25
DEFAULT_SAMPLE_SIZE=10000

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# AI Keys (if using)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Using Gunicorn (Production WSGI Server)

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Run with Gunicorn:**
```bash
gunicorn --bind 0.0.0.0:5000 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "app:create_app()"
```

**Gunicorn config file (`gunicorn.conf.py`):**
```python
bind = "0.0.0.0:5000"
workers = 4
threads = 2
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

preload_app = True
```

**Run with config:**
```bash
gunicorn -c gunicorn.conf.py "app:create_app()"
```

### Using Nginx as Reverse Proxy

**Nginx configuration (`/etc/nginx/sites-available/finese2`):**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/finese2/dashboard/static;
        expires 30d;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/finese2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

---

## Cloud Platforms

### Hugging Face Spaces

FINESE2 is already configured for Hugging Face Spaces!

**Steps:**
1. Create new Space on Hugging Face
2. Select "Docker" as SDK
3. Push code to Space repository
4. Add environment variables in Space settings
5. Deploy!

**`.env` for HF Spaces:**
```bash
SECRET_KEY=your-secret-key
SPACE_ID=your-username/finese2
```

### Heroku

**Create `Procfile`:**
```
web: gunicorn "app:create_app()"
```

**Deploy:**
```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=postgres://...
git push heroku main
```

### AWS ECS

**docker-compose.yml for ECS:**
```yaml
version: '3.8'
services:
  web:
    image: your-account.dkr.ecr.region.amazonaws.com/finese2:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/finese2
        awslogs-region: us-east-1
```

### Google Cloud Run

**Build and push:**
```bash
gcloud builds submit --tag gcr.io/project-id/finese2
gcloud run deploy finese2 \
  --image gcr.io/project-id/finese2 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY=your-key
```

### Azure App Service

**Deploy via Docker:**
```bash
az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name finese2-app \
  --deployment-container-image-name your-registry/finese2:latest

az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name finese2-app \
  --settings SECRET_KEY=your-key
```

---

## Environment Configuration

### Development
```bash
FLASK_ENV=development
FLASK_DEBUG=1
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///instance/finese2_dev.db
ENABLE_JWT=false
```

### Staging
```bash
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ENABLE_JWT=true
```

### Production
```bash
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ENABLE_JWT=true
SESSION_COOKIE_SECURE=true
JWT_COOKIE_SECURE=true
```

---

## Monitoring & Maintenance

### Health Checks

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "python_version": "3.11.0",
  "database": "connected",
  "environment": "production"
}
```

**Readiness check:** `GET /ready`

### Logging

**Configure logging in production:**
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

### Database Maintenance

**Backup SQLite:**
```bash
cp instance/finese2.db instance/finese2_backup_$(date +%Y%m%d).db
```

**Backup PostgreSQL:**
```bash
pg_dump -U username -d finese2 > backup.sql
```

**Restore:**
```bash
psql -U username -d finese2 < backup.sql
```

### Performance Monitoring

**Install monitoring tools:**
```bash
pip install prometheus-client flask-monitoring-dashboard
```

**Add metrics endpoint:**
```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
```

### Updates & Upgrades

**Update dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

**Update Docker image:**
```bash
docker-compose pull
docker-compose up -d
```

**Database migrations:**
```bash
flask db upgrade
```

---

## Troubleshooting

### Application Won't Start

**Check logs:**
```bash
docker-compose logs web
# or
tail -f app.log
```

**Common issues:**
- Missing environment variables
- Database connection errors
- Port already in use
- Permission issues

### High Memory Usage

**Solutions:**
- Reduce worker count
- Implement caching
- Optimize database queries
- Use pagination

### Slow Performance

**Optimizations:**
- Enable Redis caching
- Use connection pooling
- Add database indexes
- Implement async tasks with Celery

---

## Security Checklist

- [ ] Strong SECRET_KEY set
- [ ] HTTPS enabled
- [ ] Database credentials secured
- [ ] API keys in environment variables
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Regular security updates
- [ ] Firewall rules configured
- [ ] Backup strategy in place
- [ ] Monitoring enabled

---

## Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test health endpoint
4. Review [Troubleshooting Guide](troubleshooting.md)
5. Create GitHub issue if needed

---

**Deployment successful?** 🎉 Monitor your application and enjoy!
