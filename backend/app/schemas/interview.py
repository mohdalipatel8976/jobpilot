"""
JobPilot — Interview Schemas
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    application_id: UUID
    round_type: str = Field(..., max_length=100)
    round_number: int = Field(default=1, ge=1)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location_or_link: Optional[str] = None
    interviewer_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    preparation_notes: Optional[dict] = None


class InterviewUpdate(BaseModel):
    round_type: Optional[str] = Field(None, max_length=100)
    round_number: Optional[int] = Field(None, ge=1)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location_or_link: Optional[str] = None
    interviewer_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    preparation_notes: Optional[dict] = None


class InterviewFeedback(BaseModel):
    feedback: str
    status: str = Field(default="completed", max_length=50)


class InterviewResponse(BaseModel):
    id: UUID
    application_id: UUID
    round_type: str
    round_number: int
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location_or_link: Optional[str] = None
    interviewer_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    feedback: Optional[str] = None
    preparation_notes: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewListResponse(BaseModel):
    items: List[InterviewResponse]
    total: int
