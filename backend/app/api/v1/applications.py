"""
JobPilot — Applications API Endpoints (MongoDB Atlas Integration)
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationUpdate,
    StatusUpdate,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/applications", tags=["Applications"])

# Valid application statuses
VALID_STATUSES = {
    "draft", "applied", "screening", "interview", "assessment",
    "offer", "rejected", "withdrawn", "accepted",
}


def format_application(doc: Optional[dict]) -> Optional[dict]:
    """Format MongoDB document keys to align with standard SQL/Pydantic schemas."""
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    res["user_id"] = uuid.UUID(res["user_id"])
    if res.get("recruiter_id"):
        res["recruiter_id"] = uuid.UUID(res["recruiter_id"])
    if res.get("resume_id"):
        res["resume_id"] = uuid.UUID(res["resume_id"])
    return res


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List applications with filtering, search, sorting, and pagination."""
    filter_query = {"user_id": str(current_user.id)}

    # Filters
    if status:
        filter_query["status"] = status
    if company:
        filter_query["company_name"] = {"$regex": company, "$options": "i"}
    if priority:
        filter_query["priority"] = priority
    if search:
        filter_query["$or"] = [
            {"company_name": {"$regex": search, "$options": "i"}},
            {"job_title": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}},
        ]

    # Count total
    total = await db.applications.count_documents(filter_query)

    # Sorting direction
    direction = -1 if sort_order == "desc" else 1

    # Paginate and query
    offset = (page - 1) * page_size
    cursor = (
        db.applications.find(filter_query)
        .sort(sort_by, direction)
        .skip(offset)
        .limit(page_size)
    )
    
    applications = await cursor.to_list(length=page_size)

    return ApplicationListResponse(
        items=[ApplicationResponse.model_validate(format_application(app)) for app in applications],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Create a new job application."""
    if data.status and data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    now = datetime.now(timezone.utc)
    app_id = str(uuid.uuid4())
    
    app_doc = {
        "_id": app_id,
        "user_id": str(current_user.id),
        "recruiter_id": str(data.recruiter_id) if data.recruiter_id else None,
        "resume_id": str(data.resume_id) if data.resume_id else None,
        "company_name": data.company_name,
        "job_title": data.job_title,
        "job_url": data.job_url,
        "job_description_raw": data.job_description_raw,
        "job_description_parsed": data.job_description_parsed,
        "status": data.status or "draft",
        "priority": data.priority or "medium",
        "source": data.source,
        "technologies": data.technologies or [],
        "salary_range": data.salary_range,
        "location": data.location,
        "work_type": data.work_type,
        "employment_type": data.employment_type,
        "seniority_level": data.seniority_level,
        "experience_years": data.experience_years,
        "experience_summary": data.experience_summary,
        "applied_date": datetime.combine(data.applied_date, datetime.min.time(), tzinfo=timezone.utc) if data.applied_date else None,
        "deadline": datetime.combine(data.deadline, datetime.min.time(), tzinfo=timezone.utc) if data.deadline else None,
        "notes": data.notes,
        "created_at": now,
        "updated_at": now,
    }

    await db.applications.insert_one(app_doc)
    return format_application(app_doc)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get a single application by ID."""
    app = await db.applications.find_one(
        {"_id": str(application_id), "user_id": str(current_user.id)}
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return format_application(app)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: uuid.UUID,
    data: ApplicationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Update an existing application."""
    app = await db.applications.find_one(
        {"_id": str(application_id), "user_id": str(current_user.id)}
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    # Convert date objects to datetime for Mongo compatibility
    for key in ["applied_date", "deadline"]:
        if key in update_data and update_data[key]:
            update_data[key] = datetime.combine(update_data[key], datetime.min.time(), tzinfo=timezone.utc)

    # Convert UUIDs to string
    for key in ["recruiter_id", "resume_id"]:
        if key in update_data and update_data[key]:
            update_data[key] = str(update_data[key])

    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.applications.update_one(
        {"_id": str(application_id)},
        {"$set": update_data}
    )
    
    updated = await db.applications.find_one({"_id": str(application_id)})
    return format_application(updated)


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_status(
    application_id: uuid.UUID,
    data: StatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Update application status with optional notes."""
    if data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    app = await db.applications.find_one(
        {"_id": str(application_id), "user_id": str(current_user.id)}
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    notes = app.get("notes") or ""
    if data.notes:
        notes = f"{notes}\n[Status → {data.status}] {data.notes}".strip()

    update_data = {
        "status": data.status,
        "notes": notes,
        "updated_at": datetime.now(timezone.utc)
    }

    await db.applications.update_one(
        {"_id": str(application_id)},
        {"$set": update_data}
    )
    
    updated = await db.applications.find_one({"_id": str(application_id)})
    return format_application(updated)


@router.delete("/{application_id}", response_model=MessageResponse)
async def delete_application(
    application_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Delete an application (hard delete)."""
    app = await db.applications.find_one(
        {"_id": str(application_id), "user_id": str(current_user.id)}
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    await db.applications.delete_one({"_id": str(application_id)})
    return MessageResponse(message="Application deleted successfully")
