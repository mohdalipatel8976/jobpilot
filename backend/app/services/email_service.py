"""
JobPilot — Email Service (MongoDB Atlas Integration)
Integrates with the Gmail API to poll, parse, and auto-classify recruiter emails.
"""

import base64
import logging
import uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, Optional

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.services.ai_service import classify_email_content, parse_job_description
from app.services.notification_service import create_notification

logger = logging.getLogger("jobpilot.email")


async def _get_gmail_access_token() -> str:
    """Request a fresh Google OAuth2 access token using the configured refresh token."""
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": settings.GMAIL_CLIENT_ID,
        "client_secret": settings.GMAIL_CLIENT_SECRET,
        "refresh_token": settings.GMAIL_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, data=payload)
        response.raise_for_status()
        data = response.json()
        return data["access_token"]


def _extract_body_text(payload: Dict[str, Any]) -> str:
    """Recursively extract plain text or HTML body from Gmail message payload."""
    body_data = ""
    
    # Check body direct data
    body = payload.get("body", {})
    if body.get("data"):
        try:
            return base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="ignore")
        except Exception:
            pass
            
    # Traverse parts recursively
    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            try:
                body_data += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            except Exception:
                pass
        elif mime_type == "text/html" and part.get("body", {}).get("data") and not body_data:
            try:
                body_data += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            except Exception:
                pass
        elif part.get("parts"):
            body_data += _extract_body_text(part)
            
    return body_data


async def match_email_to_application(
    db: AsyncIOMotorDatabase, user_id: uuid.UUID, company_name: Optional[str], subject: str, body: str
) -> Optional[dict]:
    """Smart matching logic to link an email to an existing user application in MongoDB."""
    # 1. Direct search by company name if AI identified it
    if company_name:
        app = await db.applications.find_one({
            "user_id": str(user_id),
            "company_name": {"$regex": company_name, "$options": "i"}
        })
        if app:
            return app

    # 2. Case-insensitive substring matching in company names
    apps = await db.applications.find({"user_id": str(user_id)}).to_list(length=1000)
    for app in apps:
        comp = app["company_name"].lower()
        if len(comp) > 2 and (comp in subject.lower() or comp in body.lower()):
            return app
            
    return None


def _merge_parsed_job_data(existing: Optional[dict], parsed: Dict[str, Any]) -> dict:
    merged = dict(existing or {})
    for key, value in parsed.items():
        if value not in (None, [], ""):
            merged[key] = value
    return merged


async def upsert_application_from_email(
    db: AsyncIOMotorDatabase,
    user: dict,
    subject: str,
    body: str,
    from_address: str,
    received_at: datetime,
    classification: str,
    ai_data: Dict[str, Any],
) -> tuple[Optional[dict], bool]:
    """Create or enrich an application from parsed email/job data."""
    parsed_job = ai_data.get("job_parse") or {}
    company_name = parsed_job.get("company_name") or ai_data.get("company_name")
    job_title = parsed_job.get("job_title") or ai_data.get("job_title")

    application = await match_email_to_application(db, user["_id"], company_name, subject, body)
    if application:
        update_data: Dict[str, Any] = {}
        for field in ["company_name", "job_title", "location", "work_type", "salary_range", "source"]:
            value = parsed_job.get(field) or ai_data.get(field)
            if value and not application.get(field):
                update_data[field] = value

        for field in ["technologies", "requirements", "responsibilities", "benefits"]:
            value = parsed_job.get(field) or ai_data.get(field)
            if value and not application.get(field):
                update_data[field] = value

        parsed_snapshot = _merge_parsed_job_data(application.get("job_description_parsed"), {**ai_data, "job_parse": parsed_job})
        if parsed_snapshot != application.get("job_description_parsed"):
            update_data["job_description_parsed"] = parsed_snapshot

        if parsed_job.get("job_description") and not application.get("job_description_raw"):
            update_data["job_description_raw"] = body[:10000]

        if classification in {"confirmation", "general"} and application.get("status") in {"draft", None}:
            update_data["status"] = "applied"

        if not application.get("applied_date") and classification in {"confirmation", "general", "screening", "assessment", "interview_invite"}:
            update_data["applied_date"] = received_at

        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            await db.applications.update_one({"_id": application["_id"]}, {"$set": update_data})
            application = await db.applications.find_one({"_id": application["_id"]})

        return application, False

    if classification not in {"confirmation", "general"}:
        return None, False

    if not company_name or not job_title:
        return None, False

    now = datetime.now(timezone.utc)
    app_id = str(uuid.uuid4())
    parsed_snapshot = _merge_parsed_job_data(None, {**ai_data, "job_parse": parsed_job})
    application_doc = {
        "_id": app_id,
        "user_id": str(user["_id"]),
        "recruiter_id": None,
        "resume_id": None,
        "company_name": company_name,
        "job_title": job_title,
        "job_url": None,
        "job_description_raw": body[:10000],
        "job_description_parsed": parsed_snapshot,
        "status": "applied",
        "priority": "medium",
        "source": "email",
        "technologies": parsed_job.get("technologies") or [],
        "salary_range": parsed_job.get("salary_range"),
        "location": parsed_job.get("location"),
        "work_type": parsed_job.get("work_type"),
        "applied_date": received_at,
        "deadline": None,
        "notes": parsed_job.get("summary") or ai_data.get("summary"),
        "created_at": now,
        "updated_at": now,
    }
    await db.applications.insert_one(application_doc)
    return application_doc, True


async def process_single_message(db: AsyncIOMotorDatabase, user: dict, msg_summary: Dict[str, Any], access_token: str):
    """Fetch, parse, classify, and persist a single Gmail message in MongoDB."""
    msg_id = msg_summary["id"]
    
    # Check if message already exists
    dup = await db.email_events.find_one({"gmail_message_id": msg_id})
    if dup:
        return

    logger.info("Processing new email ID: %s for user: %s", msg_id, user.get("email"))
    
    # Fetch detail
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        msg_detail = response.json()

    # Extract headers
    headers_list = msg_detail.get("payload", {}).get("headers", [])
    subject = next((h["value"] for h in headers_list if h["name"].lower() == "subject"), "No Subject")
    from_address = next((h["value"] for h in headers_list if h["name"].lower() == "from"), "Unknown Sender")
    
    # Parse date
    internal_date_ms = int(msg_detail.get("internalDate", 0))
    received_at = datetime.fromtimestamp(internal_date_ms / 1000.0, tz=timezone.utc)
    
    # Decode body
    body = _extract_body_text(msg_detail.get("payload", {}))
    snippet = msg_detail.get("snippet", "")
    
    # Classify via AI
    classification = "general"
    ai_data = {}
    try:
        ai_data = await classify_email_content(subject, body, from_address)
        classification = ai_data.get("classification", "general")
    except Exception as e:
        logger.error("AI Email classification failed for ID %s: %s", msg_id, e)

    parsed_job = {}
    body_for_parse = f"Subject: {subject}\nFrom: {from_address}\n\n{body[:12000]}"
    should_parse_job = classification in {"confirmation", "general", "screening"} or any(
        keyword in f"{subject} {body}".lower()
        for keyword in ("job", "role", "position", "application", "opening", "career")
    )
    if should_parse_job and len(body.strip()) >= 80:
        try:
            parsed_job = await parse_job_description(body_for_parse)
        except Exception as e:
            logger.debug("Job parsing skipped for email %s: %s", msg_id, e)

    if parsed_job:
        ai_data = {**ai_data, "job_parse": parsed_job}
        
    # Match to Application
    application, created_from_email = await upsert_application_from_email(
        db=db,
        user=user,
        subject=subject,
        body=body,
        from_address=from_address,
        received_at=received_at,
        classification=classification,
        ai_data=ai_data,
    )

    if application and created_from_email:
        logger.info("Auto-created application from email: %s at %s", application.get("job_title"), application.get("company_name"))
    
    # Create Recruiter link if available
    recruiter_id = None
    if application and application.get("recruiter_id"):
        recruiter_id = application["recruiter_id"]
    else:
        rec = await db.recruiters.find_one({
            "user_id": str(user["_id"]),
            "email": {"$regex": from_address, "$options": "i"}
        })
        if rec:
            recruiter_id = rec["_id"]

    now = datetime.now(timezone.utc)
    email_event_id = str(uuid.uuid4())

    # Create EmailEvent Document
    email_event = {
        "_id": email_event_id,
        "application_id": application["_id"] if application else None,
        "recruiter_id": recruiter_id,
        "gmail_message_id": msg_id,
        "subject": subject,
        "body_snippet": snippet[:500],
        "from_address": from_address,
        "classification": classification,
        "ai_parsed_data": ai_data,
        "is_processed": True,
        "received_at": received_at,
        "processed_at": now,
        "created_at": now,
    }
    await db.email_events.insert_one(email_event)

    # Automate status updates & generate alerts based on classification
    if application:
        await handle_application_automation(db, user, application, email_event, ai_data)
    elif created_from_email:
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="system",
            title=f"📥 New job captured from email",
            message=f"Captured {ai_data.get('job_parse', {}).get('job_title', subject)} from {ai_data.get('job_parse', {}).get('company_name', from_address)} and saved it to your applications.",
            channel="dashboard,telegram",
        )
    else:
        # General email notification
        notif_msg = f"Received a '{classification}' classified email from {from_address}. Subject: {subject}"
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="system",
            title=f"📬 New Recruiter Email Classified",
            message=notif_msg,
            channel="dashboard,telegram"
        )


async def handle_application_automation(
    db: AsyncIOMotorDatabase, user: dict, application: dict, email_event: dict, ai_data: Dict[str, Any]
):
    """Execute status changes, schedule interviews, and tasks based on classification in MongoDB."""
    classification = email_event["classification"]
    company = application["company_name"]
    title = application["job_title"]
    now = datetime.now(timezone.utc)

    if classification == "interview_invite":
        # Only act on interview invites with sufficient confidence
        confidence = email_event.get("ai_parsed_data", {}).get("confidence", 0.5)
        if confidence < 0.70:
            logger.warning(
                "Low-confidence interview_invite (%.2f) for '%s' — reclassifying as confirmation to avoid false positive.",
                confidence, email_event.get("subject", "")
            )
            # Treat as confirmation instead - don't spam wrong alerts
            await create_notification(
                db,
                user_id=uuid.UUID(user["_id"]),
                notification_type="system",
                title=f"📬 Email Update from {company}",
                message=f"Received an email from {company} for {title}. Review it in your email tracking dashboard.",
                application_id=uuid.UUID(application["_id"]),
                channel="dashboard"
            )
            return
        
        # 1. Update status
        notes = application.get("notes") or ""
        notes = f"{notes}\n[Status → interview] Auto status transition from recruiter email".strip()
        
        await db.applications.update_one(
            {"_id": application["_id"]},
            {"$set": {"status": "interview", "notes": notes, "updated_at": now}}
        )
        
        # 2. Schedule Interview record
        interview_date_str = ai_data.get("interview_date")
        scheduled_at = None
        if interview_date_str:
            try:
                scheduled_at = datetime.fromisoformat(interview_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass
                
        interview_id = str(uuid.uuid4())
        interview = {
            "_id": interview_id,
            "application_id": application["_id"],
            "round_type": ai_data.get("interview_type", "technical"),
            "round_number": 1,
            "scheduled_at": scheduled_at or now,
            "location_or_link": "Check email invitation details",
            "interviewer_name": ai_data.get("interviewer_name") or "HR Team",
            "status": "scheduled",
            "notes": f"Auto-generated from email: {email_event['subject']}",
            "created_at": now,
            "updated_at": now
        }
        await db.interviews.insert_one(interview)
        
        # 3. Create high-priority alerts
        alert_msg = (
            f"🎉 Great news! *{company}* invited you for an interview ({interview['round_type']})!\n\n"
            f"Interviewer: {interview['interviewer_name']}\n"
            f"Time: {scheduled_at.strftime('%Y-%m-%d %I:%M %p') if scheduled_at else 'Please verify details'}\n\n"
            f"Check your dashboard to prepare notes and view details."
        )
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="interview",
            title=f"📅 Interview Scheduled at {company}!",
            message=alert_msg,
            application_id=uuid.UUID(application["_id"]),
            channel="dashboard,telegram"
        )

    elif classification == "rejection":
        notes = application.get("notes") or ""
        notes = f"{notes}\n[Status → rejected] Auto status transition from recruiter email rejection".strip()

        await db.applications.update_one(
            {"_id": application["_id"]},
            {"$set": {"status": "rejected", "notes": notes, "updated_at": now}}
        )
        
        alert_msg = (
            f"😔 We're sorry to hear that. You received a rejection update for *{company}* — {title}.\n\n"
            f"Don't lose momentum, there are plenty of other opportunities in your queue! Let's keep applying."
        )
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="rejection",
            title=f"❌ Application Update: {company}",
            message=alert_msg,
            application_id=uuid.UUID(application["_id"]),
            channel="dashboard,telegram"
        )
        
    elif classification == "offer":
        notes = application.get("notes") or ""
        notes = f"{notes}\n[Status → offer] Auto status transition from recruiter email offer".strip()

        await db.applications.update_one(
            {"_id": application["_id"]},
            {"$set": {"status": "offer", "notes": notes, "updated_at": now}}
        )
        
        alert_msg = (
            f"🏆 CONGRATULATIONS! 🌟 You have received an offer from *{company}* for the *{title}* role!\n\n"
            f"Check your dashboard immediately to track details, deadline, and compose your response strategy!"
        )
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="offer",
            title=f"🏆 Offer Received from {company}!!!",
            message=alert_msg,
            application_id=uuid.UUID(application["_id"]),
            channel="dashboard,telegram"
        )
        
    elif classification == "assessment":
        notes = application.get("notes") or ""
        notes = f"{notes}\n[Status → assessment] Auto status transition from recruiter assessment request".strip()

        await db.applications.update_one(
            {"_id": application["_id"]},
            {"$set": {"status": "assessment", "notes": notes, "updated_at": now}}
        )
        
        alert_msg = (
            f"🧪 Action Required: *{company}* sent a coding or technical assessment for *{title}*.\n\n"
            f"Check your deadlines and block out time to complete it."
        )
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="assessment",
            title=f"🧪 Tech Assessment: {company}",
            message=alert_msg,
            application_id=uuid.UUID(application["_id"]),
            channel="dashboard,telegram"
        )

    elif classification == "screening":
        notes = application.get("notes") or ""
        notes = f"{notes}\n[Status → screening] Recruiter reached out for a screening call".strip()

        await db.applications.update_one(
            {"_id": application["_id"]},
            {"$set": {"status": "screening", "notes": notes, "updated_at": now}}
        )

        alert_msg = (
            f"📞 *{company}* wants to schedule a screening/intro call for *{title}*.\n\n"
            f"Check your email and reply to arrange a time!"
        )
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="screening",
            title=f"📞 Screening Call: {company}",
            message=alert_msg,
            application_id=uuid.UUID(application["_id"]),
            channel="dashboard,telegram"
        )

    elif classification == "confirmation":
        # Application received — just a quiet dashboard note, no Telegram alert
        await create_notification(
            db,
            user_id=uuid.UUID(user["_id"]),
            notification_type="system",
            title=f"✅ Application Acknowledged by {company}",
            message=f"{company} confirmed they received your application for {title}. They will review and reach out if there's a match.",
            application_id=uuid.UUID(application["_id"]),
            channel="dashboard"
        )

    # General auto-generated follow-up reminder
    if classification in {"rejection", "interview_invite", "assessment", "confirmation"}:
        due_date = date.today()
        follow_up_id = str(uuid.uuid4())
        follow_up = {
            "_id": follow_up_id,
            "application_id": application["_id"],
            "type": "email",
            "due_date": datetime.combine(due_date, datetime.min.time(), tzinfo=timezone.utc),
            "status": "pending",
            "notes": f"Auto-generated action: Review recruiter email classification '{classification}' and update logs.",
            "is_auto_generated": True,
            "completed_at": None,
            "created_at": now
        }
        await db.follow_ups.insert_one(follow_up)


async def poll_gmail_inbox(db: AsyncIOMotorDatabase) -> int:
    """Fetch new emails, run classification pipeline, and trigger CRM automations in MongoDB."""
    if not (settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET and settings.GMAIL_REFRESH_TOKEN):
        logger.debug("Gmail integration credentials are not fully defined. Skipping poll.")
        return 0

    try:
        users = await db.users.find({"is_active": True}).to_list(length=1000)
        if not users:
            return 0
            
        access_token = await _get_gmail_access_token()
        
        total_processed = 0
        for user in users:
            url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "maxResults": 10,
                "q": "subject:(interview OR application OR rejection OR offer OR assessment OR update OR received OR confirmed OR screening OR invitation)",
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers, params=params)
                if not res.is_success:
                    logger.error("Failed to query Gmail list: %s", res.text)
                    continue
                messages = res.json().get("messages", [])

            for msg in messages:
                try:
                    await process_single_message(db, user, msg, access_token)
                    total_processed += 1
                except Exception as e:
                    logger.exception("Error processing Gmail message %s: %s", msg.get("id"), e)
                    
        return total_processed
    except Exception as e:
        logger.exception("Failed in poll_gmail_inbox cycle: %s", e)
        return 0
