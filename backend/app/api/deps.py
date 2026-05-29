"""
JobPilot — Shared API Dependencies (MongoDB Atlas Integration)
"""

import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.user import UserResponse
from app.core.config import settings


def format_user(user_doc: dict) -> dict:
    if not user_doc:
        return {}
    res = dict(user_doc)
    res["id"] = uuid.UUID(res["_id"])
    return res



# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserResponse:
    """
    Validate JWT token and return the current authenticated user.
    Supports secure server-to-server fallback for background automation tools.
    """
    token = credentials.credentials

    # 1. Server-to-server secure bypass for background cron scripts (like n8n)
    if settings.TELEGRAM_WEBHOOK_SECRET and token == settings.TELEGRAM_WEBHOOK_SECRET:
        user = await db.users.find_one({"is_active": True})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active user found for system token",
            )
        return UserResponse.model_validate(format_user(user))

    # 2. Standard JWT access token validation
    payload = decode_token(token)

    # Ensure it's an access token, not a refresh token
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use an access token.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    user = await db.users.find_one({"_id": user_id})

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    formatted = format_user(user)
    return UserResponse.model_validate(formatted)


async def get_admin_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Ensure the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
