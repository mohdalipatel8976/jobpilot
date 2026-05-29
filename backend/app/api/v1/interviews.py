"""
JobPilot — Interviews API Endpoints (MongoDB Atlas Integration)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.interview import (
    InterviewCreate,
    InterviewFeedback,
    InterviewListResponse,
    InterviewResponse,
    InterviewUpdate,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/interviews", tags=["Interviews"])


def format_interview(doc: Optional[dict]) -> Optional[dict]:
    """Helper to convert MongoDB _id to standard UUID id field for response matching."""
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    res["application_id"] = uuid.UUID(res["application_id"])
    return res


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    application_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all interviews for the current user's applications."""
    # Find all application IDs for this user
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    filter_query = {"application_id": {"$in": app_ids}}
    
    if application_id:
        filter_query["application_id"] = str(application_id)
    if status_filter:
        filter_query["status"] = status_filter

    cursor = db.interviews.find(filter_query).sort("scheduled_at", -1)
    interviews = await cursor.to_list(length=1000)

    return InterviewListResponse(
        items=[InterviewResponse.model_validate(format_interview(i)) for i in interviews],
        total=len(interviews),
    )


@router.get("/upcoming", response_model=InterviewListResponse)
async def upcoming_interviews(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get upcoming interviews sorted by date."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    now = datetime.now(timezone.utc)
    filter_query = {
        "application_id": {"$in": app_ids},
        "scheduled_at": {"$gte": now},
        "status": "scheduled",
    }

    cursor = db.interviews.find(filter_query).sort("scheduled_at", 1).limit(limit)
    interviews = await cursor.to_list(length=limit)

    return InterviewListResponse(
        items=[InterviewResponse.model_validate(format_interview(i)) for i in interviews],
        total=len(interviews),
    )


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    data: InterviewCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Create a new interview for an application."""
    # Verify the application belongs to the user
    app = await db.applications.find_one(
        {"_id": str(data.application_id), "user_id": str(current_user.id)}
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    now = datetime.now(timezone.utc)
    interview_id = str(uuid.uuid4())
    
    # Scheduled at conversion
    scheduled_at = datetime.combine(data.scheduled_at, datetime.min.time(), tzinfo=timezone.utc) if isinstance(data.scheduled_at, datetime) else data.scheduled_at

    interview_doc = {
        "_id": interview_id,
        "application_id": str(data.application_id),
        "round_type": data.round_type,
        "round_number": data.round_number,
        "scheduled_at": scheduled_at,
        "duration_minutes": data.duration_minutes,
        "location_or_link": data.location_or_link,
        "interviewer_name": data.interviewer_name,
        "status": data.status or "scheduled",
        "notes": data.notes,
        "feedback": None,
        "preparation_notes": {},
        "created_at": now,
        "updated_at": now,
    }

    await db.interviews.insert_one(interview_doc)
    return format_interview(interview_doc)


@router.patch("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: uuid.UUID,
    data: InterviewUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Update an interview."""
    # Find active application list to secure endpoint
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    interview = await db.interviews.find_one(
        {"_id": str(interview_id), "application_id": {"$in": app_ids}}
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    update_data = data.model_dump(exclude_unset=True)
    if "scheduled_at" in update_data and update_data["scheduled_at"]:
        # Standardize timezone handling
        pass

    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.interviews.update_one(
        {"_id": str(interview_id)},
        {"$set": update_data}
    )

    updated = await db.interviews.find_one({"_id": str(interview_id)})
    return format_interview(updated)


@router.patch("/{interview_id}/feedback", response_model=InterviewResponse)
async def add_feedback(
    interview_id: uuid.UUID,
    data: InterviewFeedback,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Add feedback after an interview."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    interview = await db.interviews.find_one(
        {"_id": str(interview_id), "application_id": {"$in": app_ids}}
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    update_data = {
        "feedback": data.feedback,
        "status": data.status,
        "updated_at": datetime.now(timezone.utc)
    }

    await db.interviews.update_one(
        {"_id": str(interview_id)},
        {"$set": update_data}
    )

    updated = await db.interviews.find_one({"_id": str(interview_id)})
    return format_interview(updated)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Delete an interview."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    interview = await db.interviews.find_one(
        {"_id": str(interview_id), "application_id": {"$in": app_ids}}
    )
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    await db.interviews.delete_one({"_id": str(interview_id)})
