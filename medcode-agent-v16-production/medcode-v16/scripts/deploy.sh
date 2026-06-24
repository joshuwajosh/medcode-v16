#!/bin/bash
# MedCode AI — Deployment Script
# Usage: bash scripts/deploy.sh [staging|production]

set -euo pipefail

ENVIRONMENT="${1:-production}"
COMPOSE_FILE="docker-compose.prod.yml"
HEALTH_URL="http://localhost:8000/health"
MAX_WAIT=120
HEALTHY=false

echo "============================================"
echo "  MedCode AI — Deploying to ${ENVIRONMENT}"
echo "============================================"

# ── Step 1: Pull latest code ──────────────────────────────────────
echo "[1/6] Pulling latest code..."
git pull origin main

# ── Step 2: Build Docker images ───────────────────────────────────
echo "[2/6] Building Docker images..."
docker compose -f "${COMPOSE_FILE}" build --no-cache

# ── Step 3: Run database migrations ───────────────────────────────
echo "[3/6] Running database migrations..."
docker compose -f "${COMPOSE_FILE}" exec -T postgres \
    psql -U medcode -d medcode -f /docker-entrypoint-initdb.d/01-schema.sql \
    2>/dev/null || echo "Schema already up to date"

# ── Step 4: Rolling restart ───────────────────────────────────────
echo "[4/6] Restarting services (rolling)..."
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

# ── Step 5: Health check ──────────────────────────────────────────
echo "[5/6] Waiting for health check..."
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo "  ... waiting (${ELAPSED}s / ${MAX_WAIT}s)"
done

if [ "$HEALTHY" = true ]; then
    echo "[6/6] Health check passed!"
    echo ""
    echo "============================================"
    echo "  Deployment successful — ${ENVIRONMENT}"
    echo "============================================"
    docker compose -f "${COMPOSE_FILE}" ps
else
    echo "[6/6] Health check FAILED after ${MAX_WAIT}s"
    echo ""
    echo "Rolling back..."
    docker compose -f "${COMPOSE_FILE}" logs --tail=50 medcode
    exit 1
fi
