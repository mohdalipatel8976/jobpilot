"""
JobPilot — Async MongoDB Atlas Database Driver & Session Factory
Uses Motor for high-performance non-blocking MongoDB interactions.
"""

import logging
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger("jobpilot.database")

# Global variables for MongoDB Client and Database
mongodb_client: AsyncIOMotorClient | None = None
db_instance: AsyncIOMotorDatabase | None = None


def get_mongodb_client() -> AsyncIOMotorClient:
    """Retrieve or initialize the active MongoDB client instance."""
    global mongodb_client
    if mongodb_client is not None:
        return mongodb_client

    if not settings.MONGODB_URL:
        raise ValueError("MONGODB_URL is not configured in the environment settings.")

    # Initialize motor async client
    mongodb_client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        maxPoolSize=50,
        minPoolSize=10,
        serverSelectionTimeoutMS=5000,
    )
    logger.info("MongoDB Async Client initialized.")
    return mongodb_client


def get_db_instance() -> AsyncIOMotorDatabase:
    """Retrieve the active MongoDB database instance."""
    global db_instance
    if db_instance is not None:
        return db_instance

    client = get_mongodb_client()
    db_instance = client[settings.MONGODB_DB_NAME]
    return db_instance


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    FastAPI dependency yielding the MongoDB database instance.
    No explicit commit/rollback required in standard document CRUD.
    """
    db = get_db_instance()
    yield db


async def init_db():
    """Verify connectivity to MongoDB Atlas by pinging the cluster."""
    client = get_mongodb_client()
    try:
        # Ping command requires admin database context or general connection test
        await client.admin.command("ping")
        logger.info("✅ Successfully pinged MongoDB Atlas cluster. Connection verified!")
    except Exception as e:
        logger.warning("⚠️ Failed to connect to MongoDB Atlas cluster at startup: %s", e)


async def close_db():
    """Dispose database connections safely during server shutdown."""
    global mongodb_client, db_instance
    if mongodb_client:
        logger.info("Closing MongoDB client connections...")
        mongodb_client.close()
        mongodb_client = None
        db_instance = None
        logger.info("🔴 MongoDB connections closed.")
