# JobPilot — Intelligent Job Application Tracker

JobPilot is a lightweight, production-ready application to track job applications, automatically parse job details from recruiter emails using Google Gemini, and receive Telegram notifications for important events. It's designed for jobseekers and hiring teams who want a single place to manage applications, follow-ups, interviews, and insights.

## Key Features

- Centralized tracking of job applications and statuses
- LLM-powered parsing of job descriptions (company, title, seniority, experience, employment type)
- Automatic ingestion and upsert from Gmail recruiter emails
- Telegram notifications for new leads and reminders
- Production-ready Docker Compose setup for easy deployment

## Professional Project Name

JobPilot — Intelligent Job Application Tracker

## Architecture Overview

- Backend: FastAPI (Python) providing REST APIs and workers
- Frontend: Next.js (TypeScript) with App Router and a modern UI
- LLM: Google Gemini (`gemini-2.5-flash`) for parsing and insights
- Storage: MongoDB for persistent data; Redis for caching
- Deployment: Docker & Docker Compose; optional GitHub Actions deployment to VPS

## Quickstart (Developer)

1. Copy production template and fill secrets:

```bash
cp .env.production.example .env
# Edit .env and set MONGODB_URL, REDIS_URL, GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, GMAIL_*
```

2. Start locally (development):

```bash
docker compose up --build
```

3. Start production stack locally (uses `docker-compose.prod.yml`):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Production Deployment (VPS)

- Use `infrastructure/scripts/provision_vps.sh` to bootstrap a Debian/Ubuntu VPS and deploy to `/opt/jobpilot`.
- GitHub Actions workflow `.github/workflows/deploy.yml` can SSH to the VPS and run the deploy steps (configure secrets in repository settings).

## Environment Variables

See `.env.production.example` for required production variables. Important ones include:

- `MONGODB_URL`, `REDIS_URL` — use managed services (Atlas/Managed Redis) when possible
- `GEMINI_API_KEY`, `GEMINI_MODEL` — ensure Generative Language API is enabled and billing is configured
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_USER_EMAIL`

## Security & Best Practices

- Do not commit `.env` or any secrets to version control.
- Use managed DB services for production and restrict network access.
- Restrict the Gemini API key to the Generative Language API and rotate keys periodically.
- Serve traffic behind HTTPS (use Nginx + Certbot or a cloud load balancer).

## Contributing

1. Fork and create a feature branch
2. Open a pull request
3. Run tests and include coverage where applicable

## Recruiter Pitch & Social Copy

Use the copy below when sharing your project with recruiters, on LinkedIn, or in a portfolio.

Impression (one-line headline):

"JobPilot — AI-driven job application tracker that automatically parses recruiter emails and keeps you on top of opportunities."

Short pitch (for LinkedIn or email):

"I built JobPilot to help active job-seekers move faster: it ingests recruiter emails, uses Google Gemini to parse job details (title, company, seniority, required experience), and centralizes follow-ups and interview scheduling — all with Telegram notifications for instant action. Open-source and production-ready."

Suggested LinkedIn post (engagement-focused):

"After months of chaotic spreadsheets and missed follow-ups, I built JobPilot — an AI-powered job application tracker that automatically parses recruiter emails, extracts role details using Google Gemini, and sends instant Telegram alerts for high-priority leads. If you're hiring or recruiting, I'd love to show you a demo. #jobsearch #ai #productivity #recruiting"

Top comments / replies you can seed or expect:

- "Would be great to try — does it support Gmail OAuth?"
- "This would save me hours — how do you handle PII and security?"
- "Any plans to add LinkedIn integration?"

Suggested high-engagement CTA (in comments):

"DM me your email if you'd like a 10-minute demo — I can show how JobPilot reduces missed opportunities and speeds follow-ups."

## Contact

For demos and collaboration, open an issue or contact: maintainers@yourdomain.com

---

Project files updated: see the production template `.env.production.example` and the VPS provisioning script at `infrastructure/scripts/provision_vps.sh`.
# ⚡ JobPilot — AI-Powered Job Application Management Platform

A production-grade, AI-powered CRM for managing your entire job search — from tracking applications to parsing job descriptions with local LLMs, automating email monitoring, and generating actionable analytics.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐
│  Next.js     │────▶│  Nginx   │────▶│  FastAPI      │
│  Frontend    │     │  Proxy   │     │  Backend      │
│  (Port 3000) │     │  (80/443)│     │  (Port 8000)  │
└─────────────┘     └──────────┘     └──────┬───────┘
                                            │
                    ┌───────────────────────┼───────────────────┐
                    │                       │                   │
              ┌─────▼─────┐          ┌──────▼──────┐     ┌─────▼─────┐
              │ PostgreSQL │          │    Redis     │     │  Gemini   │
              │ (Port 5432)│          │ (Port 6379)  │     │ (cloud)   │
              └────────────┘          └──────────────┘     └───────────┘
         ┌──────────┐        ┌────────────┐       ┌──────────┐
         │   n8n    │        │ Prometheus │       │ Grafana  │
         │(Port 5678)│       │(Port 9090) │       │(Port 3001)│
         └──────────┘        └────────────┘       └──────────┘
```

## 🚀 Quick Start (Local Development)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Git](https://git-scm.com/)

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd n8n_job_posting
cp .env.example .env
# Edit .env with your values (defaults work for local dev)
```

### 2. Start all services

```bash
docker compose up -d
```

### 3. Configure Gemini API key

Add your Gemini API key to `.env` as `GEMINI_API_KEY` (see `.env.example`).

### 4. Access the platform

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost |
| **API Docs** | http://localhost/api/docs |
| **n8n Workflows** | http://localhost:5678 |
| **Grafana** | http://localhost:3001 |
| **Prometheus** | http://localhost:9090 |

## 📂 Project Structure

```
├── backend/          FastAPI application
│   ├── app/
│   │   ├── api/      API routes (v1)
│   │   ├── core/     Config, security, database
│   │   ├── models/   SQLAlchemy ORM models
│   │   ├── schemas/  Pydantic request/response
│   │   ├── services/ Business logic
│   │   └── prompts/  LLM prompt templates
│   └── alembic/      Database migrations
├── frontend/         Next.js application
│   └── src/
│       ├── app/      Pages (App Router)
│       ├── components/ UI components
│       ├── lib/      Utilities & API client
│       └── types/    TypeScript types
├── infrastructure/   DevOps configs
│   ├── nginx/        Reverse proxy
│   ├── prometheus/   Metrics
│   ├── grafana/      Dashboards
│   └── scripts/      Deploy & backup scripts
├── workflows/        n8n workflow JSONs
├── database/         DB init scripts
├── docker-compose.yml
└── docker-compose.prod.yml
```

## 🔧 Development Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart a service
docker compose restart backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Generate a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Run backend tests
docker compose exec backend pytest tests/ -v

# Stop all services
docker compose down

# Stop and remove volumes (CAUTION: deletes data)
docker compose down -v
```

## 🚢 Production Deployment

```bash
# On your DigitalOcean VPS:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use the deploy script:
./infrastructure/scripts/deploy.sh
```

## 📡 API Endpoints

Full interactive API documentation available at `/api/docs` (Swagger UI) and `/api/redoc`.

## 🤖 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS v4, ShadCN UI |
| Backend | FastAPI, SQLAlchemy 2, asyncpg, Alembic |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| AI/LLM | Gemini (Google Generative) |
| Automation | n8n |
| Proxy | Nginx |
| Monitoring | Prometheus + Grafana |
| Containers | Docker + Docker Compose |

## 📝 License

MIT
