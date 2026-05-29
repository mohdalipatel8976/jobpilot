#!/usr/bin/env bash
set -euo pipefail

# Idempotent VPS provisioning + deploy script for JobPilot
# Usage: run as root (or with sudo) on the VPS after adjusting REPO_URL

REPO_URL=${REPO_URL:-"https://github.com/your-org-or-user/n8n_job_posting.git"}
APP_DIR=/opt/jobpilot
SERVICE_USER=jobpilot

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root or with sudo." >&2
  exit 1
fi

echo "==> Ensuring user ${SERVICE_USER} exists"
if ! id -u ${SERVICE_USER} >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" ${SERVICE_USER}
  usermod -aG sudo ${SERVICE_USER}
fi

echo "==> Installing prerequisites"
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release git

echo "==> Installing Docker (if missing)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sh /tmp/get-docker.sh
  rm /tmp/get-docker.sh
fi

echo "==> Ensuring Docker Compose plugin is available"
if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y docker-compose-plugin
fi

echo "==> Preparing application directory: ${APP_DIR}"
mkdir -p ${APP_DIR}
chown ${SERVICE_USER}:${SERVICE_USER} ${APP_DIR}

if [ ! -d "${APP_DIR}/.git" ]; then
  echo "==> Cloning repository ${REPO_URL} into ${APP_DIR}"
  sudo -u ${SERVICE_USER} git clone ${REPO_URL} ${APP_DIR}
else
  echo "==> Repository already exists — fetching latest"
  cd ${APP_DIR}
  sudo -u ${SERVICE_USER} git fetch --all
  sudo -u ${SERVICE_USER} git reset --hard origin/main || true
fi

cd ${APP_DIR}

if [ ! -f .env ]; then
  if [ -f .env.production.example ]; then
    cp .env.production.example .env
    echo "Created .env from .env.production.example — edit ${APP_DIR}/.env and add secrets." >&2
  else
    echo "No .env.production.example found; please create ${APP_DIR}/.env with production secrets." >&2
  fi
fi

chown ${SERVICE_USER}:${SERVICE_USER} .env || true

echo "==> Pulling and starting services via docker compose"
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull || true
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans

echo "==> Deployment finished — edit ${APP_DIR}/.env and run the compose command again if you change secrets."
