"""
JobPilot — Analytics API Endpoints (MongoDB Atlas Integration)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import cache_get, cache_set
from app.schemas.common import (
    AnalyticsOverview,
    PlatformPerformance,
    StatusBreakdown,
    TrendDataPoint,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get high-level analytics overview for the dashboard."""
    cache_key = f"analytics:overview:{current_user.id}"
    cached = await cache_get(cache_key)
    if cached:
        return AnalyticsOverview(**cached)

    # 1. Total applications
    total = await db.applications.count_documents({"user_id": str(current_user.id)})

    # 2. Status counts
    pipeline = [
        {"$match": {"user_id": str(current_user.id)}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    cursor = db.applications.aggregate(pipeline)
    rows = await cursor.to_list(length=100)
    status_counts = {item["_id"]: item["count"] for item in rows}

    interviews_count = status_counts.get("interview", 0) + status_counts.get("assessment", 0)
    offers = status_counts.get("offer", 0) + status_counts.get("accepted", 0)
    rejections = status_counts.get("rejected", 0)
    pending = status_counts.get("applied", 0) + status_counts.get("screening", 0) + status_counts.get("draft", 0)

    # 3. Total interviews
    apps = await db.applications.find({"user_id": str(current_user.id)}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]
    total_interviews = await db.interviews.count_documents({"application_id": {"$in": app_ids}})

    # 4. Response rate
    responded = total - pending
    response_rate = round((responded / total * 100) if total > 0 else 0, 1)

    # 5. Interview conversion rate
    interview_rate = round((total_interviews / total * 100) if total > 0 else 0, 1)

    result = AnalyticsOverview(
        total_applications=total,
        total_interviews=total_interviews,
        total_offers=offers,
        total_rejections=rejections,
        total_pending=pending,
        response_rate=response_rate,
        interview_conversion_rate=interview_rate,
    )

    await cache_set(cache_key, result.model_dump(), ttl=300)
    return result


@router.get("/status-breakdown", response_model=list[StatusBreakdown])
async def get_status_breakdown(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get application count per status."""
    pipeline = [
        {"$match": {"user_id": str(current_user.id)}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    cursor = db.applications.aggregate(pipeline)
    rows = await cursor.to_list(length=100)
    total = sum(r["count"] for r in rows)

    return [
        StatusBreakdown(
            status=row["_id"],
            count=row["count"],
            percentage=round((row["count"] / total * 100) if total > 0 else 0, 1),
        )
        for row in rows
    ]


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get application count trends over time."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    cursor = db.applications.find({
        "user_id": str(current_user.id),
        "created_at": {"$gte": start_date}
    })
    applications = await cursor.to_list(length=10000)

    trends = {}
    for app in applications:
        # standard date formatting
        created_at = app["created_at"]
        if isinstance(created_at, str):
            day_str = created_at[:10]
        else:
            day_str = created_at.strftime("%Y-%m-%d")
        trends[day_str] = trends.get(day_str, 0) + 1

    return [
        TrendDataPoint(date=d, count=c)
        for d, c in sorted(trends.items())
    ]


@router.get("/platform-performance", response_model=list[PlatformPerformance])
async def get_platform_performance(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get performance metrics per platform source."""
    pipeline = [
        {"$match": {"user_id": str(current_user.id)}},
        {"$group": {
            "_id": "$source",
            "total": {"$sum": 1},
            "responded": {
                "$sum": {
                    "$cond": [
                        {"$in": ["$status", ["interview", "assessment", "offer", "accepted"]]},
                        1,
                        0
                    ]
                }
            }
        }}
    ]
    cursor = db.applications.aggregate(pipeline)
    rows = await cursor.to_list(length=100)

    # Sort in memory descending
    rows.sort(key=lambda x: x["total"], reverse=True)

    return [
        PlatformPerformance(
            platform=row["_id"] or "Unknown",
            applications=row["total"],
            responses=row["responded"],
            response_rate=round((row["responded"] / row["total"] * 100) if row["total"] > 0 else 0, 1),
        )
        for row in rows
    ]


@router.get("/heatmap")
async def get_heatmap(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get application activity heatmap data."""
    start_date = datetime.now(timezone.utc) - timedelta(days=365)

    cursor = db.applications.find({
        "user_id": str(current_user.id),
        "created_at": {"$gte": start_date}
    })
    applications = await cursor.to_list(length=10000)

    heatmap_data = {}
    for app in applications:
        created_at = app["created_at"]
        if isinstance(created_at, str):
            day_str = created_at[:10]
        else:
            day_str = created_at.strftime("%Y-%m-%d")
        heatmap_data[day_str] = heatmap_data.get(day_str, 0) + 1

    return [{"date": d, "count": c} for d, c in sorted(heatmap_data.items())]
