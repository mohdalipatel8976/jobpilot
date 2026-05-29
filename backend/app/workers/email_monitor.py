"""
JobPilot — Background Email Monitor Worker
Periodically polls the Gmail inbox for new job updates and processes them.
"""

import asyncio
import logging

from app.core.config import settings
from app.core.database import get_db_instance
from app.services.email_service import poll_gmail_inbox

logger = logging.getLogger("jobpilot.worker.email")

# Global reference to control worker task execution
monitor_task: asyncio.Task | None = None
running = False


async def email_monitor_loop():
    """Infinite background loop to poll recruiter emails periodically."""
    global running
    running = True
    logger.info("Email Monitor background worker started.")

    # Small initial delay to allow FastAPI and database connections to fully warm up
    await asyncio.sleep(10)

    while running:
        logger.info("Executing periodic Gmail polling cycle...")
        
        try:
            db = get_db_instance()
            processed_count = await poll_gmail_inbox(db)
            if processed_count > 0:
                logger.info("Gmail poll complete. Processed %d new recruiter emails.", processed_count)
            else:
                logger.debug("Gmail poll complete. No new messages found.")
        except Exception as e:
            logger.exception("Unexpected error inside email monitor worker polling cycle: %s", e)

        # Configurable wait period (default: 5 minutes)
        interval = settings.EMAIL_CHECK_INTERVAL_SECONDS
        logger.debug("Sleeping for %d seconds until next Gmail poll.", interval)
        
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Email Monitor worker sleep interrupted. Shutting down...")
            break

    logger.info("Email Monitor background worker terminated.")


def start_email_monitor():
    """Start the email monitor loop as an asyncio background task."""
    global monitor_task, running
    if monitor_task is not None and not monitor_task.done():
        logger.warning("Email Monitor worker is already running.")
        return

    running = True
    monitor_task = asyncio.create_task(email_monitor_loop())


async def stop_email_monitor():
    """Stop the email monitor loop and cancel the background task."""
    global monitor_task, running
    logger.info("Stopping Email Monitor background worker...")
    running = False
    
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        monitor_task = None
        
    logger.info("Email Monitor background worker stopped.")
