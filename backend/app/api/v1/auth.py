"""
JobPilot — Auth API Endpoints (MongoDB Atlas Integration)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def format_user(user_doc: Optional[dict]) -> Optional[dict]:
    """Helper to convert MongoDB _id to standard UUID id field for response matching."""
    if not user_doc:
        return None
    user_doc["id"] = uuid.UUID(user_doc["_id"])
    return user_doc


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user document
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    user_doc = {
        "_id": user_id,
        "email": data.email,
        "hashed_password": hash_password(data.password),
        "full_name": data.full_name,
        "role": "user",
        "preferences": {},
        "telegram_chat_id": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    await db.users.insert_one(user_doc)

    # Generate tokens
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Authenticate and get JWT tokens."""
    user = await db.users.find_one({"email": data.email})

    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(subject=user["_id"])
    refresh_token = create_refresh_token(subject=user["_id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Refresh an expired access token using a refresh token."""
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected refresh token.",
        )

    user_id = payload.get("sub")
    user = await db.users.find_one({"_id": user_id})

    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    # Rotate tokens
    new_access_token = create_access_token(subject=user["_id"])
    new_refresh_token = create_refresh_token(subject=user["_id"])

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


# Standard mock dependency for active document endpoints, utilizing get_db directly
async def get_current_user_from_mongo(
    token_payload: dict = Depends(decode_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """Dependency to retrieve the current user inside routes from MongoDB."""
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return format_user(user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Update the current user's profile."""
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.users.update_one(
        {"_id": str(current_user.id)},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one({"_id": str(current_user.id)})
    return format_user(updated_user)
