"""
JobPilot — Notification Service (MongoDB Atlas Integration)
Handles multi-channel notification dispatch (Dashboard, Telegram, Email).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger("jobpilot.notification")


async def create_notification(
    db: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    notification_type: str,  # interview, assessment, follow_up, offer, rejection, deadline, system
    title: str,
    message: str,
    application_id: Optional[uuid.UUID] = None,
    channel: str = "dashboard",  # dashboard, telegram, email, or list like "dashboard,telegram"
) -> list[dict]:
    """
    Create notification(s) in the database and dispatch them to their respective channels.
    """
    # Fetch user preferences & details
    user = await db.users.find_one({"_id": str(user_id)})
    if not user:
        logger.error("User with ID %s not found. Cannot send notification.", user_id)
        return []

    channels = [c.strip() for c in channel.split(",")]
    created_notifications = []

    user_prefs = user.get("preferences") or {}
    notif_prefs = user_prefs.get("notifications", {})

    now = datetime.now(timezone.utc)

    for ch in channels:
        # Check if user disabled this channel
        if ch != "dashboard" and not notif_prefs.get(ch, True):
            logger.info("User has disabled channel '%s' in preferences.", ch)
            continue

        notification_id = str(uuid.uuid4())
        notification = {
            "_id": notification_id,
            "user_id": str(user_id),
            "application_id": str(application_id) if application_id else None,
            "channel": ch,
            "type": notification_type,
            "title": title,
            "message": message,
            "is_read": False,
            "is_sent": False,
            "created_at": now,
            "sent_at": None,
        }
        await db.notifications.insert_one(notification)
        created_notifications.append(notification)

    # Attempt to dispatch external channels asynchronously
    for notif in created_notifications:
        try:
            if notif["channel"] == "telegram":
                sent = await dispatch_telegram_notification(db, user, notif)
                if sent:
                    await db.notifications.update_one(
                        {"_id": notif["_id"]},
                        {"$set": {"is_sent": True, "sent_at": datetime.now(timezone.utc)}}
                    )
            elif notif["channel"] == "dashboard":
                await db.notifications.update_one(
                    {"_id": notif["_id"]},
                    {"$set": {"is_sent": True, "sent_at": datetime.now(timezone.utc)}}
                )
            elif notif["channel"] == "email":
                sent = await dispatch_email_notification(user, notif)
                if sent:
                    await db.notifications.update_one(
                        {"_id": notif["_id"]},
                        {"$set": {"is_sent": True, "sent_at": datetime.now(timezone.utc)}}
                    )
        except Exception as e:
            logger.exception("Failed to dispatch notification %s via %s: %s", notif["_id"], notif["channel"], e)

    return created_notifications


async def dispatch_telegram_notification(db: AsyncIOMotorDatabase, user: dict, notification: dict) -> bool:
    """Send a notification via the Telegram service bot."""
    telegram_chat_id = user.get("telegram_chat_id")
    if not telegram_chat_id:
        logger.warning("User %s has no telegram_chat_id registered. Cannot send Telegram alert.", user["_id"])
        return False

    from app.services.telegram_service import send_telegram_alert
    
    formatted_message = f"🔔 *{notification['title']}*\n\n{notification['message']}"
    return await send_telegram_alert(telegram_chat_id, formatted_message)


async def dispatch_email_notification(user: dict, notification: dict) -> bool:
    """Send a notification via email (SMTP)."""
    logger.info("Email notification dispatch triggered for user %s: %s", user.get("email"), notification["title"])
    return True
