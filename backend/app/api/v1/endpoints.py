"""
JobPilot — Follow-Ups, Notifications, Resumes, Email Events, AI API Endpoints (MongoDB Atlas Integration)
"""

import os
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.common import (
    EmailEventListResponse,
    EmailEventResponse,
    FollowUpCreate,
    FollowUpListResponse,
    FollowUpResponse,
    FollowUpUpdate,
    MessageResponse,
    NotificationListResponse,
    NotificationResponse,
    ResumeResponse,
    ResumeUpdate,
    UnreadCountResponse,
    AIParseJobRequest,
    AIClassifyEmailRequest,
    AIInsightRequest,
    AIParseResponse,
    AIHealthResponse,
    RecruiterCreate,
    RecruiterResponse,
)
from app.schemas.user import UserResponse

# ============================================================
# Format Helpers
# ============================================================

def format_follow_up(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    res["application_id"] = uuid.UUID(res["application_id"])
    # Handle dates from Mongo datetime
    if isinstance(res.get("due_date"), datetime):
        res["due_date"] = res["due_date"].date()
    elif isinstance(res.get("due_date"), str):
        res["due_date"] = date.fromisoformat(res["due_date"][:10])
    return res


def format_notification(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    res["user_id"] = uuid.UUID(res["user_id"])
    if res.get("application_id"):
        res["application_id"] = uuid.UUID(res["application_id"])
    return res


def format_resume(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    res["user_id"] = uuid.UUID(res["user_id"])
    return res


def format_email_event(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    if res.get("application_id"):
        res["application_id"] = uuid.UUID(res["application_id"])
    if res.get("recruiter_id"):
        res["recruiter_id"] = uuid.UUID(res["recruiter_id"])
    return res


def format_recruiter(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    res = dict(doc)
    res["id"] = uuid.UUID(res["_id"])
    res["user_id"] = uuid.UUID(res["user_id"])
    return res


# ============================================================
# Follow-Ups Router
# ============================================================
follow_ups_router = APIRouter(prefix="/follow-ups", tags=["Follow-Ups"])


@follow_ups_router.get("", response_model=FollowUpListResponse)
async def list_follow_ups(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all follow-ups for the current user's applications."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    filter_query = {"application_id": {"$in": app_ids}}
    if status_filter:
        filter_query["status"] = status_filter

    cursor = db.follow_ups.find(filter_query).sort("due_date", 1)
    items = await cursor.to_list(length=1000)

    formatted_items = []
    for item in items:
        f = format_follow_up(item)
        if f:
            f["telegram_chat_id"] = current_user.telegram_chat_id
            formatted_items.append(FollowUpResponse.model_validate(f))

    return FollowUpListResponse(
        items=formatted_items,
        total=len(formatted_items),
    )


@follow_ups_router.get("/due", response_model=FollowUpListResponse)
async def due_follow_ups(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get due and overdue follow-ups."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    today = datetime.combine(date.today(), datetime.max.time(), tzinfo=timezone.utc)
    filter_query = {
        "application_id": {"$in": app_ids},
        "due_date": {"$lte": today},
        "status": {"$in": ["pending", "overdue"]},
    }

    cursor = db.follow_ups.find(filter_query).sort("due_date", 1)
    items = await cursor.to_list(length=1000)

    formatted_items = []
    for item in items:
        f = format_follow_up(item)
        if f:
            f["telegram_chat_id"] = current_user.telegram_chat_id
            formatted_items.append(FollowUpResponse.model_validate(f))

    return FollowUpListResponse(
        items=formatted_items,
        total=len(formatted_items),
    )


@follow_ups_router.post("", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
async def create_follow_up(
    data: FollowUpCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Create a new follow-up."""
    app = await db.applications.find_one(
        {"_id": str(data.application_id), "user_id": str(current_user.id)}
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    now = datetime.now(timezone.utc)
    due_datetime = datetime.combine(data.due_date, datetime.min.time(), tzinfo=timezone.utc)
    follow_up_id = str(uuid.uuid4())

    follow_up_doc = {
        "_id": follow_up_id,
        "application_id": str(data.application_id),
        "type": data.type,
        "due_date": due_datetime,
        "status": data.status or "pending",
        "message_template": data.message_template,
        "notes": data.notes,
        "is_auto_generated": data.is_auto_generated or False,
        "completed_at": None,
        "created_at": now,
    }

    await db.follow_ups.insert_one(follow_up_doc)
    return format_follow_up(follow_up_doc)


@follow_ups_router.patch("/{follow_up_id}/complete", response_model=FollowUpResponse)
async def complete_follow_up(
    follow_up_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Mark a follow-up as completed."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    follow_up = await db.follow_ups.find_one(
        {"_id": str(follow_up_id), "application_id": {"$in": app_ids}}
    )
    if not follow_up:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")

    update_data = {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc)
    }

    await db.follow_ups.update_one(
        {"_id": str(follow_up_id)},
        {"$set": update_data}
    )

    updated = await db.follow_ups.find_one({"_id": str(follow_up_id)})
    return format_follow_up(updated)


# ============================================================
# Notifications Router
# ============================================================
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List notifications for the current user."""
    filter_query = {"user_id": str(current_user.id)}
    if is_read is not None:
        filter_query["is_read"] = is_read

    total = await db.notifications.count_documents(filter_query)
    
    unread_count = await db.notifications.count_documents(
        {"user_id": str(current_user.id), "is_read": False}
    )

    offset = (page - 1) * page_size
    cursor = db.notifications.find(filter_query).sort("created_at", -1).skip(offset).limit(page_size)
    items = await cursor.to_list(length=page_size)

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(format_notification(n)) for n in items],
        total=total,
        unread_count=unread_count,
    )


@notifications_router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get unread notification count."""
    count = await db.notifications.count_documents(
        {"user_id": str(current_user.id), "is_read": False}
    )
    return UnreadCountResponse(count=count)


@notifications_router.patch("/{notification_id}/read", response_model=MessageResponse)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Mark a notification as read."""
    res = await db.notifications.update_one(
        {"_id": str(notification_id), "user_id": str(current_user.id)},
        {"$set": {"is_read": True}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return MessageResponse(message="Notification marked as read")


@notifications_router.post("/read-all", response_model=MessageResponse)
async def mark_all_read(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Mark all notifications as read."""
    await db.notifications.update_many(
        {"user_id": str(current_user.id), "is_read": False},
        {"$set": {"is_read": True}}
    )
    return MessageResponse(message="All notifications marked as read")


# ============================================================
# Resumes Router
# ============================================================
resumes_router = APIRouter(prefix="/resumes", tags=["Resumes"])


@resumes_router.get("", response_model=list[ResumeResponse])
async def list_resumes(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all resumes for the current user."""
    cursor = db.resumes.find({"user_id": str(current_user.id)}).sort("is_default", -1)
    resumes = await cursor.to_list(length=100)
    return [ResumeResponse.model_validate(format_resume(r)) for r in resumes]


@resumes_router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    title: str = Query(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Upload a resume file (PDF or DOCX)."""
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed",
        )

    upload_dir = "/app/uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)

    ext = "pdf" if "pdf" in file.content_type else "docx"
    filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    file_path = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    now = datetime.now(timezone.utc)
    resume_id = str(uuid.uuid4())

    resume_doc = {
        "_id": resume_id,
        "user_id": str(current_user.id),
        "title": title,
        "file_path": file_path,
        "file_type": ext,
        "metadata": {},
        "is_default": False,
        "usage_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    await db.resumes.insert_one(resume_doc)
    return format_resume(resume_doc)


@resumes_router.patch("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: uuid.UUID,
    data: ResumeUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Update resume metadata or set as default."""
    resume = await db.resumes.find_one({"_id": str(resume_id), "user_id": str(current_user.id)})
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        # Unset all others first
        await db.resumes.update_many(
            {"user_id": str(current_user.id), "_id": {"$ne": str(resume_id)}},
            {"$set": {"is_default": False}}
        )

    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.resumes.update_one(
        {"_id": str(resume_id)},
        {"$set": update_data}
    )

    updated = await db.resumes.find_one({"_id": str(resume_id)})
    return format_resume(updated)


# ============================================================
# Email Events Router
# ============================================================
email_events_router = APIRouter(prefix="/email-events", tags=["Email Events"])


@email_events_router.get("", response_model=EmailEventListResponse)
async def list_email_events(
    classification: Optional[str] = Query(None),
    is_processed: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List email events linked to the user's applications."""
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]

    # Return events matching users applications, or unassigned ones
    filter_query = {
        "$or": [
            {"application_id": {"$in": app_ids}},
            {"application_id": None}
        ]
    }

    if classification:
        filter_query["classification"] = classification
    if is_processed is not None:
        filter_query["is_processed"] = is_processed

    total = await db.email_events.count_documents(filter_query)

    offset = (page - 1) * page_size
    cursor = db.email_events.find(filter_query).sort("received_at", -1).skip(offset).limit(page_size)
    items = await cursor.to_list(length=page_size)

    return EmailEventListResponse(
        items=[EmailEventResponse.model_validate(format_email_event(e)) for e in items],
        total=total,
    )


# ============================================================
# Recruiters Router
# ============================================================
recruiters_router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


@recruiters_router.get("", response_model=list[RecruiterResponse])
async def list_recruiters(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all recruiters for the current user."""
    cursor = db.recruiters.find({"user_id": str(current_user.id)}).sort("last_contacted", -1)
    recruiters = await cursor.to_list(length=1000)
    return [RecruiterResponse.model_validate(format_recruiter(r)) for r in recruiters]


@recruiters_router.post("", response_model=RecruiterResponse, status_code=status.HTTP_201_CREATED)
async def create_recruiter(
    data: RecruiterCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Create a new recruiter contact."""
    now = datetime.now(timezone.utc)
    rec_id = str(uuid.uuid4())

    rec_doc = {
        "_id": rec_id,
        "user_id": str(current_user.id),
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "linkedin_url": data.linkedin_url,
        "phone": data.phone,
        "notes": data.notes,
        "interaction_count": 0,
        "last_contacted": None,
        "created_at": now,
    }

    await db.recruiters.insert_one(rec_doc)
    return format_recruiter(rec_doc)


# ============================================================
# AI Router
# ============================================================
ai_router = APIRouter(prefix="/ai", tags=["AI"])


@ai_router.post("/parse-job", response_model=AIParseResponse)
async def parse_job(
    data: AIParseJobRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Parse a job description using the configured AI provider."""
    from app.services.ai_service import parse_job_description

    try:
        result = await parse_job_description(data.text)
        return AIParseResponse(success=True, data=result)
    except Exception as e:
        return AIParseResponse(success=False, error=str(e))


@ai_router.post("/classify-email", response_model=AIParseResponse)
async def classify_email(
    data: AIClassifyEmailRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Classify an email using AI."""
    from app.services.ai_service import classify_email_content

    try:
        result = await classify_email_content(data.subject, data.body, data.from_address)
        return AIParseResponse(success=True, data=result)
    except Exception as e:
        return AIParseResponse(success=False, error=str(e))


@ai_router.post("/generate-insights", response_model=AIParseResponse)
async def generate_insights(
    data: AIInsightRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Generate AI-powered insights from application data."""
    from app.services.ai_service import generate_user_insights

    try:
        result = await generate_user_insights(current_user.id, data.time_range_days, db)
        return AIParseResponse(success=True, data=result)
    except Exception as e:
        return AIParseResponse(success=False, error=str(e))


@ai_router.get("/health", response_model=AIHealthResponse)
async def ai_health():
    """Check the configured AI provider health and model availability."""
    from app.services.ai_service import check_gemini_health

    return await check_gemini_health()


@ai_router.get("/integrations-status")
async def integrations_status(
    current_user: UserResponse = Depends(get_current_user),
):
    """Check integration configuration and health status."""
    from app.core.config import settings
    
    gmail_connected = bool(
        settings.GMAIL_CLIENT_ID and 
        settings.GMAIL_CLIENT_SECRET and 
        settings.GMAIL_REFRESH_TOKEN
    )
    
    return {
        "ai": {
            "connected": bool(settings.GEMINI_API_KEY),
            "provider": "gemini",
            "model": settings.GEMINI_MODEL,
        },
        "gmail": {
            "connected": gmail_connected,
            "email": settings.GMAIL_USER_EMAIL or "Not configured"
        },
        "telegram": {
            "connected": bool(current_user.telegram_chat_id),
            "chat_id": current_user.telegram_chat_id or "Not configured"
        }
    }

