# MedCode AI V19 — Deployment Checklist

## Pre-Deployment Verification

All tests pass:
- [x] Pipeline: 20/20 (100%) strict matching
- [x] Clinical parser: 108/108 (100%)
- [x] HIPAA compliance: 20/20 (100%)
- [x] Module imports: 31/31
- [x] End-to-end claim: 8/8 stages pass

## Quick Start (Development)

```bash
# Clone and start
git clone https://github.com/joshuwajosh/medcode-v16.git
cd medcode-v16
cp .env.example .env
docker-compose -f docker-compose.dev.yml up

# Access:
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8000/dashboard/
```

## Production Deployment

### 1. Server Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo apt install docker-compose-plugin
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with production values:
# - DATABASE_URL=postgresql://medcode:password@postgres:5432/medcode
# - JWT_SECRET=<random-64-char-string>
# - MEDCODE_SECRET_KEY=<random-64-char-string>
# - MEDCODE_ENCRYPTION_KEY=<Fernet-key>
# - DB_PASSWORD=<strong-password>
```

### 3. SSL Certificates
```bash
# Option A: Self-signed (testing)
cd nginx/ssl && bash generate-ssl.sh

# Option B: Let's Encrypt (production)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
# Copy certs to nginx/ssl/
```

### 4. Deploy
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Or use deploy script
bash scripts/deploy.sh production
```

### 5. Verify
```bash
# Health check
curl http://localhost/health

# API docs
open http://localhost/docs

# Dashboard
open http://localhost/dashboard/
```

## Architecture

```
┌─────────┐     ┌──────────┐     ┌──────────┐
│  Nginx  │────▶│ MedCode  │────▶│ Postgres │
│  :80/443│     │  App     │     │  :5432   │
└─────────┘     │  :8000   │     └──────────┘
                └──────────┘
                     │
                ┌────┴────┐
                │  Redis  │
                │  :6379  │
                └─────────┘
```

## API Endpoints (100+)

| Category | Endpoints |
|----------|-----------|
| Auth | /api/v19/auth/login, /register, /refresh, /logout |
| Coding | /api/v19/code, /batch, /pipeline/stages |
| Clinical | /api/v19/clinical-notes/parse |
| Billing | /api/v19/billing/generate-claim, /validate-claim, /cms1500, /ub04, /edi-837, /submit-claim |
| Batch | /api/v19/billing/batch, /batch/{id}, /batches |
| Reports | /api/v19/reports/hipaa-compliance, /claim-summary, /coding-accuracy |
| Compliance | /api/v19/compliance/hipaa-report, /audit-summary, /stats |
| Dashboard | /api/v19/dashboard/stats, /activity, /charts |
| Health | /health, /ready, /live |

## Monitoring

- Logs: /var/log/medcode/ (JSON structured)
- Audit: /var/log/medcode/audit.log (90-day retention)
- Metrics: /metrics endpoint (Prometheus format)
- Dashboard: http://localhost/dashboard/

## Backup

```bash
# Database backup
bash scripts/backup.sh

# Automated daily backup (add to crontab)
0 2 * * * /app/scripts/backup.sh
```

## Rollback

```bash
# If deployment fails
bash scripts/deploy.sh rollback
```

## System Inventory

| Component | Count |
|-----------|-------|
| Python files | 878 |
| API endpoints | 100+ |
| Training cases | 2,000 |
| CPT codes | 5,377 |
| ICD-10 codes | 27,390 |
| Test scenarios | 148 |
| Security modules | 12 |
| Billing modules | 9 |
| Dashboard tabs | 6 |
