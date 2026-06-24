#!/bin/bash
# MedCode AI — Database Backup Script
# Usage: bash scripts/backup.sh [--upload-s3]

set -euo pipefail

BACKUP_DIR="/opt/medcode/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/medcode_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
UPLOAD_S3=false

if [ "${1:-}" = "--upload-s3" ] && [ -n "$S3_BUCKET" ]; then
    UPLOAD_S3=true
fi

echo "============================================"
echo "  MedCode AI — Database Backup"
echo "============================================"

# ── Ensure backup directory exists ────────────────────────────────
mkdir -p "${BACKUP_DIR}"

# ── Dump and compress ─────────────────────────────────────────────
echo "Backing up database..."
docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U medcode -d medcode --clean --if-exists \
    | gzip > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ── Upload to S3 (optional) ──────────────────────────────────────
if [ "$UPLOAD_S3" = true ]; then
    echo "Uploading to s3://${S3_BUCKET}/backups/..."
    aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/backups/$(basename ${BACKUP_FILE})" \
        --storage-class STANDARD_IA
    echo "Upload complete."
fi

# ── Retention policy ──────────────────────────────────────────────
echo "Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "medcode_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(find "${BACKUP_DIR}" -name "medcode_*.sql.gz" | wc -l)
echo "${REMAINING} backup(s) retained."

echo ""
echo "============================================"
echo "  Backup complete"
echo "============================================"
