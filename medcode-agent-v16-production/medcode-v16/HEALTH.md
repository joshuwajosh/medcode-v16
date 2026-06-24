# MedCode AI — Deployment Guide

## Quick Start (Local Development)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Start development environment
docker compose -f docker-compose.dev.yml up -d

# 3. Access
# App: http://localhost:8000
# Docs: http://localhost:8000/docs
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

## Local Development (without Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-postgresql.txt

# 2. Configure
cp .env.example .env
# Set DATABASE_URL to sqlite:///medcode.db for local testing

# 3. Run
python main.py
# or
uvicorn main:app --reload --port 8000
```

## Production Deployment

### Prerequisites
- Docker and Docker Compose v2+
- SSL certificates (see below)
- SSH access to deployment server

### Steps

```bash
# 1. Clone on server
git clone <repo-url> /opt/medcode
cd /opt/medcode

# 2. Configure environment
cp .env.example .env
# Edit .env with production values (secrets, DB passwords, etc.)

# 3. Generate SSL certificates (development)
bash nginx/ssl/generate-ssl.sh

# 4. Deploy
bash scripts/deploy.sh production
```

### Using the deploy script

The `scripts/deploy.sh` script handles:
1. Pulling latest code from main
2. Building Docker images
3. Running database migrations
4. Rolling restart of services
5. Health check verification
6. Automatic rollback on failure

```bash
bash scripts/deploy.sh staging      # Deploy to staging
bash scripts/deploy.sh production   # Deploy to production
```

## SSL Certificate Setup

### Development (self-signed)
```bash
bash nginx/ssl/generate-ssl.sh
```
This creates self-signed certs in `nginx/ssl/`. Uncomment the HTTPS server block in `nginx/nginx.conf`.

### Production (Let's Encrypt)
```bash
# Install certbot
apt install certbot

# Get certificate
certbot certonly --webroot -w /var/www/certbot -d yourdomain.com

# Copy to nginx ssl directory
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/

# Auto-renew
echo "0 0 1 * * certbot renew --post-hook 'docker compose restart nginx'" | crontab -
```

## Database Migrations

Schema is applied automatically via `schema.sql` mounted as a Docker entrypoint init script.

For manual migrations:
```bash
# Apply schema
docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U medcode -d medcode -f /docker-entrypoint-initdb.d/01-schema.sql

# Backup before changes
bash scripts/backup.sh

# Backup with S3 upload
bash scripts/backup.sh --upload-s3
```

### Backup Schedule
```bash
# Add to crontab for daily backups at 2 AM
echo "0 2 * * * /opt/medcode/scripts/backup.sh --upload-s3" | crontab -
```

Backups are kept for 30 days by default. Configure via `RETENTION_DAYS` in the script.

## Monitoring

### Health Checks
- Application: `curl http://localhost:8000/health`
- PostgreSQL: `docker compose exec postgres pg_isready -U medcode`
- Redis: `docker compose exec redis redis-cli ping`

### Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f medcode

# Structured logs (JSON)
docker compose -f docker-compose.prod.yml logs -f medcode | python -m json.tool

# Nginx access log
docker compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/access.log
```

### Log Locations (inside containers)
- Application: `/app/logs/medcode.log`
- Errors: `/app/logs/error.log`
- Access: `/app/logs/access.log`
- Audit (HIPAA): `/app/logs/audit.log`
- Nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

## CI/CD Pipeline

### Continuous Integration (`.github/workflows/ci.yml`)
Triggered on push to main and PRs:
1. **Lint** — flake8 + mypy type checking
2. **Test** — pytest with SQLite (fast)
3. **Test (PostgreSQL)** — pytest with PostgreSQL service container
4. **Security** — bandit + safety dependency check
5. **Build** — Docker image build + push to GHCR

### Continuous Deployment (`.github/workflows/deploy.yml`)
Triggered after CI passes on main, or manual dispatch:
1. **Build & Push** — Docker image to GHCR with commit SHA tag
2. **Deploy Staging** — SSH to staging, pull + restart
3. **Deploy Production** — Manual approval gate, then deploy

### Required GitHub Secrets
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
- `PRODUCTION_HOST`, `PRODUCTION_USER`, `PRODUCTION_SSH_KEY`
- `SLACK_WEBHOOK_URL` (optional, for notifications)
- `S3_BACKUP_BUCKET` (optional, for backup uploads)

## Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Basic development setup |
| `docker-compose.dev.yml` | Development with hot reload |
| `docker-compose.prod.yml` | Production with Nginx, Redis, security |

## Resource Limits (Production)

| Service | Memory | CPU |
|---------|--------|-----|
| Nginx | 256 MB | 0.5 |
| MedCode | 2 GB | 2.0 |
| PostgreSQL | 1 GB | 1.0 |
| Redis | 512 MB | 0.5 |

Adjust in `docker-compose.prod.yml` as needed.

## Troubleshooting

### Container won't start
```bash
docker compose -f docker-compose.prod.yml logs <service>
```

### Database connection refused
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U medcode
```

### Redis connection refused
```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD ping
```

### SSL certificate issues
```bash
# Verify certificate
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Test nginx config
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Reset everything
```bash
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d --build
```
