# ⚡ JobPilot n8n Workflows

This directory contains pre-configured n8n workflow definitions to automate email monitoring, job application parsing, Telegram alerts, and task follow-ups.

## Included Workflows

1. **Email Monitoring & AI Classification (`email-monitoring.json`)**
   - **Trigger:** Scheduled cron (every 5 minutes).
   - **Operation:** Connects to Gmail, pulls recent job-related threads, calls the FastAPI AI endpoint (Gemini) to classify recruiter mail (invites, rejections, assessments, offers), and invokes the webhook to update the CRM.

2. **Job Description AI Parser (`job-parsing.json`)**
   - **Trigger:** Inbound HTTP webhook from FastAPI (upon user adding a raw job posting).
   - **Operation:** Passes raw text/URL to the AI parser (Gemini) to parse keys (company, role, location, tech stacks) and updates the relational database record.

3. **Telegram Alerts Dispatcher (`telegram-notifications.json`)**
   - **Trigger:** HTTP callback event from backend operations.
   - **Operation:** Formats the update details into a curated Markdown alert and sends it directly to the user's registered chat ID via the bot.

4. **Daily Follow-Up Reminders (`follow-up-reminders.json`)**
   - **Trigger:** Daily cron.
   - **Operation:** Polls the `/follow-ups/due` API endpoint and pushes alert lists directly to the user's Telegram.

## How to Import Workflows into n8n

1. Open your n8n dashboard (typically `http://localhost:5678` in development).
2. Go to **Workflows** → **Add Workflow** (or **New**).
3. In the top-right corner, click the **three dots menu (...)** → **Import from File**.
4. Select one of the JSON files in this directory.
5. Set up credentials for **Gmail** and **Telegram** nodes (you will need a Google OAuth Client credential and a Telegram Bot token).
6. Save and **Activate** the workflow.
