"""
JobPilot — Application Schemas
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    company_name: str = Field(..., max_length=255)
    job_title: str = Field(..., max_length=255)
    job_url: Optional[str] = None
    job_description_raw: Optional[str] = None
    job_description_parsed: Optional[dict] = None
    status: str = Field(default="draft", max_length=50)
    priority: str = Field(default="medium", max_length=20)
    source: Optional[str] = Field(None, max_length=100)
    technologies: Optional[List[str]] = None
    salary_range: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    work_type: Optional[str] = Field(None, max_length=50)
    employment_type: Optional[str] = Field(None, max_length=50)
    seniority_level: Optional[str] = Field(None, max_length=50)
    experience_years: Optional[str] = Field(None, max_length=100)
    experience_summary: Optional[str] = Field(None, max_length=255)
    applied_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = None
    recruiter_id: Optional[UUID] = None
    resume_id: Optional[UUID] = None


class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    job_url: Optional[str] = None
    job_description_raw: Optional[str] = None
    job_description_parsed: Optional[dict] = None
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    source: Optional[str] = Field(None, max_length=100)
    technologies: Optional[List[str]] = None
    salary_range: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    work_type: Optional[str] = Field(None, max_length=50)
    employment_type: Optional[str] = Field(None, max_length=50)
    seniority_level: Optional[str] = Field(None, max_length=50)
    experience_years: Optional[str] = Field(None, max_length=100)
    experience_summary: Optional[str] = Field(None, max_length=255)
    applied_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = None
    recruiter_id: Optional[UUID] = None
    resume_id: Optional[UUID] = None


class StatusUpdate(BaseModel):
    status: str = Field(..., max_length=50)
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    recruiter_id: Optional[UUID] = None
    resume_id: Optional[UUID] = None
    company_name: str
    job_title: str
    job_url: Optional[str] = None
    job_description_raw: Optional[str] = None
    job_description_parsed: Optional[dict] = None
    status: str
    priority: str
    source: Optional[str] = None
    technologies: Optional[List[str]] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    work_type: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    experience_years: Optional[str] = None
    experience_summary: Optional[str] = None
    applied_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
