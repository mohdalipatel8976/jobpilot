"""
JobPilot — Analytics, Notification, Resume, FollowUp, EmailEvent Schemas
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# -------------------------------------------------------
# Analytics
# -------------------------------------------------------

class AnalyticsOverview(BaseModel):
    total_applications: int = 0
    total_interviews: int = 0
    total_offers: int = 0
    total_rejections: int = 0
    total_pending: int = 0
    response_rate: float = 0.0
    interview_conversion_rate: float = 0.0


class StatusBreakdown(BaseModel):
    status: str
    count: int
    percentage: float


class TrendDataPoint(BaseModel):
    date: str
    count: int


class PlatformPerformance(BaseModel):
    platform: str
    applications: int
    responses: int
    response_rate: float


class AnalyticsDashboard(BaseModel):
    overview: AnalyticsOverview
    status_breakdown: List[StatusBreakdown] = []
    weekly_trend: List[TrendDataPoint] = []
    platform_performance: List[PlatformPerformance] = []


# -------------------------------------------------------
# Notification
# -------------------------------------------------------

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    application_id: Optional[UUID] = None
    channel: str
    type: str
    title: str
    message: Optional[str] = None
    is_read: bool
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    count: int


# -------------------------------------------------------
# Resume
# -------------------------------------------------------

class ResumeCreate(BaseModel):
    title: str = Field(..., max_length=255)


class ResumeUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None


class ResumeResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    file_path: str
    file_type: str
    metadata_: Optional[dict] = Field(None, alias="metadata_")
    is_default: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# -------------------------------------------------------
# Follow-Up
# -------------------------------------------------------

class FollowUpCreate(BaseModel):
    application_id: UUID
    type: str = Field(..., max_length=50)
    due_date: date
    message_template: Optional[str] = None
    notes: Optional[str] = None


class FollowUpUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    message_template: Optional[str] = None
    notes: Optional[str] = None


class FollowUpResponse(BaseModel):
    id: UUID
    application_id: UUID
    type: str
    due_date: date
    status: str
    message_template: Optional[str] = None
    notes: Optional[str] = None
    is_auto_generated: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    telegram_chat_id: Optional[str] = None

    model_config = {"from_attributes": True}


class FollowUpListResponse(BaseModel):
    items: List[FollowUpResponse]
    total: int


# -------------------------------------------------------
# Email Event
# -------------------------------------------------------

class EmailEventResponse(BaseModel):
    id: UUID
    application_id: Optional[UUID] = None
    recruiter_id: Optional[UUID] = None
    gmail_message_id: str
    subject: Optional[str] = None
    body_snippet: Optional[str] = None
    from_address: Optional[str] = None
    classification: Optional[str] = None
    ai_parsed_data: Optional[dict] = None
    is_processed: bool
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailEventListResponse(BaseModel):
    items: List[EmailEventResponse]
    total: int


# -------------------------------------------------------
# Recruiter
# -------------------------------------------------------

class RecruiterCreate(BaseModel):
    name: str = Field(..., max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class RecruiterResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    interaction_count: int
    last_contacted: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# -------------------------------------------------------
# AI
# -------------------------------------------------------

class AIParseJobRequest(BaseModel):
    text: str = Field(..., min_length=10)


class AIClassifyEmailRequest(BaseModel):
    subject: str
    body: str
    from_address: Optional[str] = None


class AIInsightRequest(BaseModel):
    time_range_days: int = Field(default=30, ge=7, le=365)


class AIParseResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AIHealthResponse(BaseModel):
    status: str
    model: str
    available: bool


# -------------------------------------------------------
# Generic
# -------------------------------------------------------

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
