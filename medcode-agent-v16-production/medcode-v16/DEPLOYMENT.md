# MedCode AI V16 — Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying MedCode AI in a production environment. The deployment uses Docker containers with PostgreSQL, Redis, and Nginx reverse proxy.

## Prerequisites

### Server Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB SSD | 100+ GB SSD |
| OS | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install additional tools
sudo apt install curl wget git certbot nginx -y
```

---

## Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/joshuwajosh/medcode-v16.git
cd medcode-v16

# Verify repository
ls -la
```

---

## Step 2: Configure Environment Variables

### 2.1 Copy Template

```bash
cp .env.example .env.production
```

### 2.2 Generate Security Keys

```bash
# Generate JWT secret (64 characters)
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT_SECRET=$JWT_SECRET"

# Generate Fernet encryption key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "MEDCODE_ENCRYPTION_KEY=$ENCRYPTION_KEY"

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32)
echo "DB_PASSWORD=$DB_PASSWORD"

# Generate Redis password
REDIS_PASSWORD=$(openssl rand -base64 24)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"

# Generate API secret key
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY"
```

### 2.3 Edit .env.production

```bash
nano .env.production
```

**Required Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://medcode:password@postgres:5432/medcode` |
| `DB_PASSWORD` | PostgreSQL password | `<strong-random-password>` |
| `REDIS_PASSWORD` | Redis password | `<random-password>` |
| `JWT_SECRET` | JWT signing key (64 chars) | `<hex-string>` |
| `SECRET_KEY` | Application secret key | `<hex-string>` |
| `MEDCODE_ENCRYPTION_KEY` | Fernet encryption key | `<fernet-key>` |

**Optional Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (empty) | AI model API key |
| `PHI_MASKING_ENABLED` | `true` | Enable PHI masking |
| `RATE_LIMIT_PER_MINUTE` | `100` | API rate limit |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SSL_CERT_PATH` | `/etc/nginx/ssl/fullchain.pem` | SSL certificate path |
| `SSL_KEY_PATH` | `/etc/nginx/ssl/privkey.pem` | SSL private key path |

---

## Step 3: SSL Certificate Setup

### Option A: Let's Encrypt (Recommended for Production)

```bash
# Install certbot
sudo apt install certbot -y

# Stop nginx if running
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
sudo chmod 600 ./nginx/ssl/*.pem

# Auto-renewal (add to crontab)
echo "0 0,12 * * * certbot renew --quiet" | sudo crontab -
```

### Option B: Self-Signed (Testing Only)

```bash
cd nginx/ssl
bash generate-ssl.sh
cd ../..
```

### Option C: Custom Certificate

```bash
# Copy your existing certificates
cp /path/to/your/cert.pem ./nginx/ssl/fullchain.pem
cp /path/to/your/key.pem ./nginx/ssl/privkey.pem
chmod 600 ./nginx/ssl/*.pem
```

---

## Step 4: Database Setup

### 4.1 Initialize Database

```bash
# Start PostgreSQL container only
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for PostgreSQL to be ready
sleep 10

# Verify PostgreSQL is running
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U medcode -d medcode

# Run schema initialization (if not auto-applied)
docker-compose -f docker-compose.prod.yml exec postgres psql -U medcode -d medcode -f /docker-entrypoint-initdb.d/01-schema.sql
```

### 4.2 Verify Database

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U medcode -d medcode

# Check tables
\dt

# Exit
\q
```

### 4.3 Database Backup Configuration

```bash
# Create backup directory
mkdir -p /opt/medcode/backups

# Add cron job for daily backups
echo "0 2 * * * docker-compose -f /opt/medcode/docker-compose.prod.yml exec -T postgres pg_dump -U medcode medcode | gzip > /opt/medcode/backups/medcode_\$(date +\%Y\%m\%d).sql.gz" | sudo crontab -
```

---

## Step 5: Deploy Services

### 5.1 Build and Start Services

```bash
# Build containers
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### 5.2 Verify Deployment

```bash
# Health check
curl -f http://localhost/health

# API documentation
curl http://localhost/docs | head -20

# Check logs
docker-compose -f docker-compose.prod.yml logs -f medcode
```

### 5.3 Create Admin User

```bash
# Access the application container
docker-compose -f docker-compose.prod.yml exec medcode bash

# Create admin user (inside container)
python -c "
from security.auth import create_admin_user
create_admin_user('admin@yourdomain.com', 'SecurePassword123!')
"

# Exit container
exit
```

---

## Step 6: Configure Monitoring

### 6.1 Enable Prometheus Metrics

```bash
# Add to .env.production
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### 6.2 Setup Log Rotation

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/medcode <<EOF
/var/log/medcode/*.log {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 0640 medcode medcode
    sharedscripts
    postrotate
        docker-compose -f /opt/medcode/docker-compose.prod.yml restart medcode
    endscript
}
EOF
```

### 6.3 Setup Uptime Monitoring

```bash
# Create monitoring script
cat > /opt/medcode/scripts/health-monitor.sh <<'EOF'
#!/bin/bash
HEALTH_URL="http://localhost/health"
ALERT_EMAIL="ops@yourdomain.com"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$response" != "200" ]; then
    echo "MedCode health check failed at $(date)" | mail -s "MedCode Alert" $ALERT_EMAIL
    docker-compose -f /opt/medcode/docker-compose.prod.yml restart medcode
fi
EOF

chmod +x /opt/medcode/scripts/health-monitor.sh

# Add to crontab (every 5 minutes)
echo "*/5 * * * * /opt/medcode/scripts/health-monitor.sh" | sudo crontab -
```

---

## Step 7: Backup Procedures

### 7.1 Manual Backup

```bash
# Full backup
bash scripts/backup.sh

# Database only
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U medcode medcode > backup_$(date +%Y%m%d).sql
```

### 7.2 Automated Backup

```bash
# Create backup script
cat > /opt/medcode/scripts/automated-backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/medcode/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose -f /opt/medcode/docker-compose.prod.yml exec -T postgres pg_dump -U medcode medcode | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Application data backup
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /opt/medcode/data

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
EOF

chmod +x /opt/medcode/scripts/automated-backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /opt/medcode/scripts/automated-backup.sh" | sudo crontab -
```

### 7.3 Restore Backup

```bash
# Restore database
gunzip < backup_20240101.sql.gz | docker-compose -f docker-compose.prod.yml exec -T postgres psql -U medcode -d medcode
```

---

## Step 8: Security Hardening

### 8.1 Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### 8.2 API Key Management

```bash
# Access admin panel
curl -X POST http://localhost/api/v19/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "password": "SecurePassword123!"}'

# Create API key for third-party integration
curl -X POST http://localhost/api/v19/api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Integration Key", "permissions": ["read", "write"]}'
```

### 8.3 HIPAA Compliance Checklist

- [ ] PHI masking enabled (`PHI_MASKING_ENABLED=true`)
- [ ] Audit logging enabled (`AUDIT_LOG_PATH=/app/logs/audit.log`)
- [ ] SSL/TLS configured for all connections
- [ ] Database encryption at rest enabled
- [ ] Access logs retained for 90 days
- [ ] Regular security audits scheduled

---

## Step 9: Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker-compose -f docker-compose.prod.yml logs medcode
```

**Database connection failed:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U medcode -d medcode
```

**SSL certificate error:**
```bash
# Verify certificate
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Check permissions
ls -la nginx/ssl/
```

**High memory usage:**
```bash
docker stats
```

### Rollback Procedure

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore previous version
git checkout <previous-tag>

# Rebuild and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

---

## Step 10: Post-Deployment Verification

```bash
# Run integration tests
export TESTING=1
python -m pytest tests/test_production_deployment.py -v

# Run HIPAA compliance tests
export TESTING=1
python -m pytest tests/test_hipaa_compliance.py -v

# Verify all endpoints
curl http://localhost/health
curl http://localhost/ready
curl http://localhost/live
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
              ┌───────▼───────┐
              │     Nginx     │
              │   :80 / :443  │
              │  (SSL/TLS)    │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │   MedCode     │
              │   Application │
              │    :8000      │
              └───┬───────┬───┘
                  │       │
          ┌───────▼───┐   │
          │ PostgreSQL │   │
          │   :5432    │   │
          └───────────┘   │
                          │
                  ┌───────▼───┐
                  │   Redis   │
                  │   :6379   │
                  └───────────┘
```

---

## API Endpoints Reference

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Health | `/health` | GET | Application health check |
| Health | `/ready` | GET | Readiness probe |
| Health | `/live` | GET | Liveness probe |
| Auth | `/api/v19/auth/login` | POST | User login |
| Auth | `/api/v19/auth/register` | POST | User registration |
| Auth | `/api/v19/auth/refresh` | POST | Refresh JWT token |
| Coding | `/api/v19/code` | POST | Code a clinical note |
| Coding | `/api/v19/code/batch` | POST | Batch coding |
| Billing | `/api/v19/billing/generate-claim` | POST | Generate claim |
| Billing | `/api/v19/billing/validate-claim` | POST | Validate claim |
| Billing | `/api/v19/billing/cms1500` | POST | Generate CMS-1500 |
| Billing | `/api/v19/billing/ub04` | POST | Generate UB-04 |
| Reports | `/api/v19/reports/hipaa-compliance` | GET | HIPAA report |
| Dashboard | `/api/v19/dashboard/stats` | GET | Dashboard statistics |
| API Keys | `/api/v19/api-keys` | GET | List API keys |
| API Keys | `/api/v19/api-keys` | POST | Create API key |

---

## Support

For issues or questions:
- Documentation: Check `/docs` endpoint
- Logs: `docker-compose -f docker-compose.prod.yml logs`
- Health: `curl http://localhost/health`
