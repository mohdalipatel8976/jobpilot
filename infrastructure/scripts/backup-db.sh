#!/bin/bash
# ============================================================
# JobPilot — Database Backup Script
# Usage: ./backup-db.sh
# ============================================================

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
BACKUP_FILE="${BACKUP_DIR}/jobpilot_${TIMESTAMP}.sql.gz"
CONTAINER_NAME="jobpilot-postgres"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "🗄️  Starting database backup..."
echo "   Container: ${CONTAINER_NAME}"
echo "   Output: ${BACKUP_FILE}"

# Perform backup
docker exec "${CONTAINER_NAME}" pg_dump \
    -U "${POSTGRES_USER:-jobpilot}" \
    -d "${POSTGRES_DB:-jobpilot}" \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}"

# Verify
if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
    echo "✅ Backup completed: ${BACKUP_FILE} (${SIZE})"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Cleanup old backups (keep last 30)
ls -t "${BACKUP_DIR}"/jobpilot_*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm
echo "🧹 Old backups cleaned (keeping last 30)"
