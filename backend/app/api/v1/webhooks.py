"""
JobPilot — Webhook Endpoints
Handles secure inbound updates from Telegram Bot API and n8n workflows.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from telegram import Update

from app.core.config import settings
from app.services.telegram_service import get_telegram_app

logger = logging.getLogger("jobpilot.webhooks")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/telegram", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    """
    Handle inbound updates forwarded by Telegram.
    Includes X-Telegram-Bot-API-Secret-Token validation for production security.
    """
    # 1. Validate Secret Token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Unauthorized webhook request. Secret token mismatch.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret token"
            )

    try:
        # 2. Parse update data
        update_data = await request.json()
        
        # 3. Retrieve python-telegram-bot application and process update
        app = get_telegram_app()
        update = Update.de_json(update_data, app.bot)
        
        # Dispatch asynchronously to registered handlers
        await app.process_update(update)
        
        return {"status": "success"}
    except Exception as e:
        logger.exception("Failed to process Telegram webhook update: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing update"
        )


@router.post("/n8n", status_code=status.HTTP_200_OK)
async def n8n_webhook(
    data: Dict[str, Any],
    authorization: str | None = Header(None)
):
    """
    Orchestration callback for n8n workflows.
    Enables workflows to feedback results like parsed job applications or email events.
    """
    # Basic auth token verification
    expected_token = settings.TELEGRAM_WEBHOOK_SECRET or "n8n_secret_token"
    if authorization != f"Bearer {expected_token}":
        logger.warning("Unauthorized n8n callback attempt.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized callback"
        )

    event_type = data.get("event")
    logger.info("Received n8n webhook callback event: %s", event_type)

    # Trigger custom workflow processing based on payload event
    # e.g., external AI parsing pipelines, bulk aggregations, or reports.
    return {
        "status": "processed",
        "event": event_type,
        "timestamp": data.get("timestamp")
    }
