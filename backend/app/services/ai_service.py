"""
JobPilot — AI Service (Gemini)
Handles all LLM interactions using Google Gemini as the single model provider.
"""

import json
import logging
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.schemas.common import AIHealthResponse

logger = logging.getLogger("jobpilot.ai")

# Gemini API endpoint template
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Request timeout (LLM can be slow)
TIMEOUT = httpx.Timeout(120.0, connect=10.0)


async def _call_gemini(prompt: str, system_prompt: str = "") -> str:
    """Send a prompt to Gemini and return the response text.

    Raises a RuntimeError if `GEMINI_API_KEY` is not configured.
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured — Gemini is required.")

    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    url = GEMINI_GENERATE_URL.format(model=settings.GEMINI_MODEL)
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": settings.GEMINI_API_KEY,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini response did not include any candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if text:
        return text

    raise ValueError("Gemini response did not include any text")


async def _call_ai_model(prompt: str, system_prompt: str = "") -> str:
    """Currently uses Gemini only."""
    return await _call_gemini(prompt, system_prompt)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response text, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    # Try to parse as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            try:
                return json.loads(text[first_brace : last_brace + 1])
            except json.JSONDecodeError:
                pass
    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


# -------------------------------------------------------
# Job Description Parser
# -------------------------------------------------------

JOB_PARSER_SYSTEM = """You are a job description parser. Extract structured data from job postings.

CRITICAL RULES:
1. Respond with ONLY valid JSON. No extra text, no explanations.
2. Extract ACTUAL values from the job description. Never return placeholder text.
3. For work_type: pick exactly ONE of "remote", "hybrid", or "onsite" based on the job description. If not mentioned, use null.
4. For seniority_level: pick exactly ONE of "intern", "junior", "mid", "senior", "lead", or "principal" based on the experience level. If unclear, use null.
5. For salary_range: extract the actual salary numbers if mentioned (e.g. "$120k-$150k"). If not mentioned, use null.
6. For location: extract the actual city/state/country. If not mentioned, use null.
7. For technologies: list the actual tech stack mentioned (e.g. ["Python", "React", "AWS"]).
8. Ignore any promotional texts, subscription offers, or unrelated content (e.g., "50% Off Premium", "Codecademy subscription").
9. Capture experience requirements exactly as stated. If a range is mentioned, keep it as text like "2-4 years".
10. job_description should be a concise plain-English summary of the role, not a copy of the full posting.

Return this JSON structure:
{
  "company_name": "actual company name from the posting",
  "job_title": "actual job title from the posting",
  "location": "actual location or null",
  "work_type": "remote or hybrid or onsite or null",
    "employment_type": "full-time or part-time or contract or internship or temporary or freelance or null",
  "salary_range": "actual salary range string or null",
  "seniority_level": "intern or junior or mid or senior or lead or principal or null",
    "experience_years": "experience requirement text or null",
    "experience_summary": "short experience requirement summary or null",
  "technologies": ["actual", "tech", "names"],
  "requirements": ["actual requirement 1", "actual requirement 2"],
  "responsibilities": ["actual responsibility 1", "actual responsibility 2"],
  "benefits": ["actual benefit 1", "actual benefit 2"],
    "job_description": "brief summary of the role and what the person will do",
  "summary": "A brief 1-2 sentence summary of the role"
}

EXAMPLE - If the job says "Software Engineer at Google, Mountain View, CA, Remote, 3+ years experience, using Python and Go":
{
  "company_name": "Google",
  "job_title": "Software Engineer",
  "location": "Mountain View, CA",
  "work_type": "remote",
    "employment_type": "full-time",
  "salary_range": null,
  "seniority_level": "mid",
    "experience_years": "3+ years",
    "experience_summary": "3+ years of experience building production systems",
  "technologies": ["Python", "Go"],
  "requirements": ["3+ years experience"],
  "responsibilities": [],
  "benefits": [],
    "job_description": "Build and ship software systems using Python and Go.",
  "summary": "Software Engineer position at Google in Mountain View, CA working with Python and Go."
}"""


def _sanitize_parsed_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up common LLM mistakes where schema descriptions are returned as literal values."""
    # Patterns that indicate the LLM echoed the schema instead of extracting real data
    garbage_patterns = [
        "string or null", "string", "actual company", "actual job",
        "actual location", "actual salary", "actual requirement",
        "actual responsibility", "actual benefit", "actual tech",
    ]

    def is_garbage(val: str) -> bool:
        lower = val.strip().lower()
        # Check if it contains pipe-delimited options (like "Remote|Hybrid|Onsite|Null")
        if "|" in lower:
            return True
        return any(p in lower for p in garbage_patterns)

    for key in ["company_name", "job_title", "location", "salary_range", "experience_years", "experience_summary", "job_description", "summary"]:
        val = result.get(key)
        if isinstance(val, str) and is_garbage(val):
            result[key] = None

    # Sanitize work_type
    wt = result.get("work_type")
    if isinstance(wt, str):
        wt_lower = wt.strip().lower()
        if wt_lower in ("remote", "hybrid", "onsite"):
            result["work_type"] = wt_lower
        else:
            result["work_type"] = None

    et = result.get("employment_type")
    if isinstance(et, str):
        et_lower = et.strip().lower().replace(" ", "-")
        if et_lower in ("full-time", "part-time", "contract", "internship", "temporary", "freelance"):
            result["employment_type"] = et_lower
        else:
            result["employment_type"] = None

    # Sanitize seniority_level
    sl = result.get("seniority_level")
    if isinstance(sl, str):
        sl_lower = sl.strip().lower()
        if sl_lower in ("intern", "junior", "mid", "senior", "lead", "principal"):
            result["seniority_level"] = sl_lower
        else:
            result["seniority_level"] = None

    # Sanitize list fields — remove garbage items
    for key in ["technologies", "requirements", "responsibilities", "benefits"]:
        val = result.get(key)
        if isinstance(val, list):
            result[key] = [item for item in val if isinstance(item, str) and not is_garbage(item)]

    return result


async def parse_job_description(text: str) -> Dict[str, Any]:
    """Parse a job description into structured data using AI."""
    logger.info("Parsing job description (%d chars)", len(text))
    prompt = f"Parse the following job description:\n\n{text}"
    response = await _call_ai_model(prompt, JOB_PARSER_SYSTEM)
    result = _extract_json(response)
    result = _sanitize_parsed_result(result)
    logger.info("Parsed job: %s at %s", result.get("job_title"), result.get("company_name"))
    return result


# -------------------------------------------------------
# Email Classifier
# -------------------------------------------------------

EMAIL_CLASSIFIER_SYSTEM = """You are a strict email classifier for job application tracking.
Classify the email into exactly ONE of these categories. Respond with valid JSON only.

CLASSIFICATION RULES (read carefully, order matters):
1. "interview_invite" - ONLY if the email explicitly invites/schedules an actual interview with a specific time/date or asks you to pick a slot. Phrases like "We'd like to invite you for an interview", "Please schedule your interview", "Interview on [date]". NOT for application acknowledgments.
2. "rejection" - The company says they won't be moving forward with your application. Phrases like "We regret to inform", "not selected", "won't be moving forward", "other candidates".
3. "offer" - A formal job offer with salary/compensation details.
4. "assessment" - A coding test, assignment, or technical assessment is being sent. Phrases like "complete this assessment", "coding challenge", "take-home test".
5. "confirmation" - Application received acknowledgment, profile received, resume received, "we'll review and get back to you". THIS IS NOT AN INTERVIEW. Phrases like "application received", "we received your profile", "we will review", "thank you for applying".
6. "screening" - Recruiter wants a quick intro call or phone screen to learn more about you.
7. "follow_up" - Follow-up on a previous application or interview.
8. "general" - Anything else recruitment-related that doesn't fit above.

CRITICAL: "Application received" or "We received your profile" emails are ALWAYS "confirmation", NEVER "interview_invite".

Return JSON:
{
  "classification": "interview_invite|rejection|offer|assessment|confirmation|screening|follow_up|general",
  "confidence": 0.0-1.0,
  "company_name": "string or null",
  "interviewer_name": "string or null",
  "interview_date": "ISO date string or null",
  "interview_type": "phone_screen|technical|behavioral|system_design|onsite|hr|final|null",
  "urgency": "high|medium|low",
  "summary": "1 sentence summary"
}"""


async def classify_email_content(
    subject: str, body: str, from_address: Optional[str] = None
) -> Dict[str, Any]:
    """Classify an email and extract relevant job application data."""
    logger.info("Classifying email: %s", subject[:80])
    prompt = f"From: {from_address or 'Unknown'}\nSubject: {subject}\n\nBody:\n{body}"
    response = await _call_ai_model(prompt, EMAIL_CLASSIFIER_SYSTEM)
    result = _extract_json(response)
    logger.info("Email classified as: %s (confidence: %s)", result.get("classification"), result.get("confidence"))
    return result


# -------------------------------------------------------
# Insight Generator
# -------------------------------------------------------

INSIGHT_SYSTEM = """You are a job search strategy advisor. Analyze the provided application data
and provide actionable insights. Respond with valid JSON only:

{
  "summary": "Brief overview of the job search status",
  "strengths": ["What's working well"],
  "weaknesses": ["What needs improvement"],
  "recommendations": ["Specific actionable recommendations"],
  "trends": ["Notable trends in the data"],
  "focus_areas": ["Areas to prioritize"],
  "predicted_timeline": "Estimated timeline to next milestone"
}"""


async def generate_user_insights(
    user_id: UUID, time_range_days: int, db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """Generate AI insights from user's application data in MongoDB."""
    from datetime import datetime, timedelta, timezone

    start_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)

    # Gather application status counts
    pipeline = [
        {"$match": {
            "user_id": str(user_id),
            "created_at": {"$gte": start_date}
        }},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    cursor = db.applications.aggregate(pipeline)
    rows = await cursor.to_list(length=100)
    status_counts = {item["_id"]: item["count"] for item in rows}

    total = sum(status_counts.values())

    # Get top sources
    source_pipeline = [
        {"$match": {
            "user_id": str(user_id),
            "created_at": {"$gte": start_date}
        }},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    source_cursor = db.applications.aggregate(source_pipeline)
    source_rows = await source_cursor.to_list(length=5)
    top_sources = {item["_id"] or "Unknown": item["count"] for item in source_rows}

    data_summary = f"""Application data for the last {time_range_days} days:
- Total applications: {total}
- Status breakdown: {json.dumps(status_counts)}
- Top sources: {json.dumps(top_sources)}
- Interview rate: {round((status_counts.get('interview', 0) + status_counts.get('assessment', 0)) / total * 100, 1) if total > 0 else 0}%
- Offer rate: {round((status_counts.get('offer', 0) + status_counts.get('accepted', 0)) / total * 100, 1) if total > 0 else 0}%
- Rejection rate: {round(status_counts.get('rejected', 0) / total * 100, 1) if total > 0 else 0}%"""

    response = await _call_gemini(data_summary, INSIGHT_SYSTEM)
    return _extract_json(response)


# -------------------------------------------------------
# Health Check
# -------------------------------------------------------


async def check_gemini_health() -> AIHealthResponse:
    """Check Gemini availability using a tiny generation request."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(
                GEMINI_GENERATE_URL.format(model=settings.GEMINI_MODEL),
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": settings.GEMINI_API_KEY,
                },
                json={
                    "contents": [{"parts": [{"text": "Respond with the word ok."}]}],
                    "generationConfig": {"maxOutputTokens": 4},
                },
            )
            response.raise_for_status()
        return AIHealthResponse(
            status="connected",
            model=settings.GEMINI_MODEL,
            available=True,
        )
    except Exception as e:
        logger.warning("Gemini health check failed: %s", e)
        return AIHealthResponse(
            status="disconnected",
            model=settings.GEMINI_MODEL,
            available=False,
        )
