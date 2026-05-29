"""
JobPilot — API v1 Router Aggregator
Collects all endpoint routers into a single v1 router.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.applications import router as applications_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.endpoints import (
    follow_ups_router,
    notifications_router,
    resumes_router,
    email_events_router,
    recruiters_router,
    ai_router,
)
from app.api.v1.webhooks import router as webhooks_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount all routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(applications_router)
api_v1_router.include_router(interviews_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(follow_ups_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(email_events_router)
api_v1_router.include_router(recruiters_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(webhooks_router)

