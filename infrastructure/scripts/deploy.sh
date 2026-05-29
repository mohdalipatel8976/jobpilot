#!/bin/bash
# ============================================================
# JobPilot — Deployment Script
# Usage: ./deploy.sh
# ============================================================

set -euo pipefail

echo "🚀 Deploying JobPilot..."

# Pull latest code
echo "📥 Pulling latest changes..."
git pull origin main

# Build and restart services
echo "🔨 Building containers..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Backup database before deploying
echo "🗄️  Creating pre-deploy backup..."
./infrastructure/scripts/backup-db.sh || echo "⚠️  Backup skipped (first deploy?)"

# Stop and restart
echo "♻️  Restarting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for health
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check health
if curl -sf http://localhost/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed — check logs"
fi

# Run migrations
echo "📊 Running database migrations..."
docker compose exec -T backend alembic upgrade head || echo "⚠️  Migration skipped"

echo ""
echo "🟢 Deployment complete!"
echo "   Frontend: http://localhost"
echo "   API Docs: http://localhost/api/docs"
echo "   n8n:      http://localhost:5678"
echo "   Grafana:  http://localhost:3001"
