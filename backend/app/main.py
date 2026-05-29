"""
JobPilot — FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis
from app.api.v1.router import api_v1_router
from app.services.telegram_service import init_telegram_bot, shutdown_telegram_bot
from app.workers.email_monitor import start_email_monitor, stop_email_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("jobpilot")


async def seed_default_user():
    """Ensure at least one active user exists in the database for system bypass authentication."""
    from app.core.database import get_db_instance
    from app.core.security import hash_password
    import uuid
    from datetime import datetime, timezone
    
    db = get_db_instance()
    
    # 1. Ensure mohdalipatel8976@gmail.com exists and is active with silent auth credentials
    primary_email = "mohdalipatel8976@gmail.com"
    hashed_pwd = hash_password("admin_password_123")
    
    primary_user = await db.users.find_one({"email": primary_email})
    if not primary_user:
        primary_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        primary_user = {
            "_id": primary_id,
            "email": primary_email,
            "hashed_password": hashed_pwd,
            "full_name": "JobPilot Admin",
            "role": "admin",
            "preferences": {},
            "telegram_chat_id": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        await db.users.insert_one(primary_user)
        logger.info(f"🌱 Seeded default active user ({primary_email}) for system token bypass")
    else:
        primary_id = primary_user["_id"]
        await db.users.update_one(
            {"_id": primary_id},
            {"$set": {"hashed_password": hashed_pwd, "is_active": True, "role": "admin"}}
        )
        logger.info(f"🌱 Synchronized silent auth credentials for active user ({primary_email})")

    # 2. Check and migrate applications from legacy admin@jobpilot.dev user if it exists
    legacy_user = await db.users.find_one({"email": "admin@jobpilot.dev"})
    if legacy_user:
        legacy_id = legacy_user["_id"]
        # Migrate applications
        migrated_apps = await db.applications.update_many(
            {"user_id": legacy_id},
            {"$set": {"user_id": primary_id}}
        )
        logger.info(f"📦 Migrated {migrated_apps.modified_count} applications from legacy admin@jobpilot.dev user to {primary_email}")
        
        # Migrate recruiters
        migrated_recs = await db.recruiters.update_many(
            {"user_id": legacy_id},
            {"$set": {"user_id": primary_id}}
        )
        logger.info(f"💼 Migrated {migrated_recs.modified_count} recruiters from legacy admin@jobpilot.dev user")
        
        # Migrate resumes
        migrated_resumes = await db.resumes.update_many(
            {"user_id": legacy_id},
            {"$set": {"user_id": primary_id}}
        )
        logger.info(f"📄 Migrated {migrated_resumes.modified_count} resumes from legacy admin@jobpilot.dev user")
        
        # Delete legacy user
        await db.users.delete_one({"_id": legacy_id})
        logger.info("🗑️ Deleted legacy admin@jobpilot.dev user document")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown events."""
    # --- Startup ---
    logger.info("🚀 Starting JobPilot Backend...")

    # Initialize database
    logger.info("Connecting to MongoDB Atlas...")
    await init_db()
    logger.info("✅ MongoDB connected")

    # Seed default user if database is empty
    try:
        await seed_default_user()
    except Exception as e:
        logger.warning(f"⚠️ Could not seed default active user (database unreachable): {e}")

    # Initialize Redis
    try:
        logger.info("Connecting to Redis...")
        await init_redis()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")

    # Initialize Telegram Bot
    try:
        logger.info("Starting Telegram Bot...")
        await init_telegram_bot()
        logger.info("✅ Telegram Bot initialized")
    except Exception as e:
        logger.warning(f"⚠️ Telegram Bot startup failed: {e}")

    # Start Email Monitor worker
    try:
        logger.info("Starting Email Monitor worker...")
        start_email_monitor()
        logger.info("✅ Email Monitor worker started")
    except Exception as e:
        logger.warning(f"⚠️ Email Monitor worker failed: {e}")

    logger.info("🟢 JobPilot Backend ready")

    yield

    # --- Shutdown ---
    logger.info("Shutting down JobPilot Backend...")
    await close_db()
    await close_redis()
    await shutdown_telegram_bot()
    await stop_email_monitor()
    logger.info("🔴 JobPilot Backend stopped")



# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Job Application Management Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Prometheus Metrics ---
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

# --- Mount API Routes ---
app.include_router(api_v1_router)


# --- Health Check ---
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
