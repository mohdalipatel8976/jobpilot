"""
JobPilot — Telegram Service (MongoDB Atlas Integration)
Handles bot commands, database queries, and notifications.
"""

import logging
import uuid
from typing import Optional
from datetime import datetime, timezone

from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Application as TelegramApp, CommandHandler, MessageHandler, filters, CallbackContext

from app.core.config import settings
from app.core.database import get_db_instance

logger = logging.getLogger("jobpilot.telegram")

# Global variables for Python Telegram Bot application and bot instances
telegram_app: Optional[TelegramApp] = None
bot_instance: Optional[Bot] = None

TELEGRAM_ADMIN_ID = 5732773323

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["📊 Stats", "📅 Interviews"], ["⏰ Follow-ups"]],
    resize_keyboard=True,
    one_time_keyboard=False
)


async def check_admin_permission(update: Update) -> bool:
    """Check if the user is the authorized admin."""
    user = update.effective_user
    if not user or user.id != TELEGRAM_ADMIN_ID:
        denied_message = (
            "🔒 *Access Denied* 🔒\n\n"
            "This bot is for personal use only. You cannot access or interact with it "
            "without admin permission."
        )
        if update.message:
            await update.message.reply_text(denied_message, parse_mode="Markdown")
        return False
    return True


async def send_telegram_alert(chat_id: str, message: str) -> bool:
    """Send a direct message alert to a Telegram user."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram Bot Token is not set. Cannot send alert.")
        return False
    try:
        global bot_instance
        if not bot_instance:
            bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot_instance.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logger.exception("Failed to send Telegram message to %s: %s", chat_id, e)
        return False


async def start_command(update: Update, context: CallbackContext):
    """Link a user account via UUID or show instructions."""
    if not await check_admin_permission(update):
        return
    chat_id = str(update.effective_chat.id)
    db = get_db_instance()

    # Automatically find the active admin/user in MongoDB and link it directly
    target_email = settings.GMAIL_USER_EMAIL or "mohdalipatel8976@gmail.com"
    user = await db.users.find_one({"email": target_email, "is_active": True})
    
    if not user:
        # Fallback to the first active user
        user = await db.users.find_one({"is_active": True})

    if not user:
        await update.message.reply_text("❌ *No active user account found in database.*", parse_mode="Markdown")
        return

    # Link in database
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"telegram_chat_id": chat_id, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Success confirmation
    await update.message.reply_text(
        f"🎉 *Success, {user.get('full_name', 'Admin')}!* Your Telegram account is now automatically linked to your JobPilot profile.\n\n"
        "You will now receive alerts for interview invites, email updates, and due follow-ups here!\n\n"
        "Use the buttons below to interact with the bot:",
        reply_markup=MAIN_KEYBOARD,
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: CallbackContext):
    """Show the user's application statistics."""
    if not await check_admin_permission(update):
        return
    chat_id = str(update.effective_chat.id)
    db = get_db_instance()
    
    user = await db.users.find_one({"telegram_chat_id": chat_id})
    if not user:
        await update.message.reply_text("⚠️ Account not linked. Use `/start` to connect your profile first.", reply_markup=MAIN_KEYBOARD)
        return
        
    # Run stats queries
    total = await db.applications.count_documents({"user_id": user["_id"]})
    
    pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    cursor = db.applications.aggregate(pipeline)
    rows = await cursor.to_list(length=100)
    status_counts = {item["_id"]: item["count"] for item in rows}
    
    response = (
        f"📊 *JobPilot Search Summary*\n"
        f"Account: {user.get('full_name')}\n"
        f"---------------------------\n"
        f"📂 *Total Applications:* {total}\n"
        f"📝 Drafts: {status_counts.get('draft', 0)}\n"
        f"📤 Applied: {status_counts.get('applied', 0)}\n"
        f"🔍 Screening: {status_counts.get('screening', 0)}\n"
        f"📅 Interviews: {status_counts.get('interview', 0)}\n"
        f"🧪 Assessments: {status_counts.get('assessment', 0)}\n"
        f"🏆 Offers: {status_counts.get('offer', 0)}\n"
        f"❌ Rejections: {status_counts.get('rejected', 0)}\n"
    )
    await update.message.reply_text(response, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")


async def interviews_command(update: Update, context: CallbackContext):
    """Show upcoming interviews."""
    if not await check_admin_permission(update):
        return
    chat_id = str(update.effective_chat.id)
    db = get_db_instance()
    
    user = await db.users.find_one({"telegram_chat_id": chat_id})
    if not user:
        await update.message.reply_text("⚠️ Account not linked. Use `/start` to connect your profile first.", reply_markup=MAIN_KEYBOARD)
        return
        
    apps = await db.applications.find({"user_id": user["_id"]}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]
    app_map = {app["_id"]: app for app in apps}

    now = datetime.now(timezone.utc)
    cursor = db.interviews.find({
        "application_id": {"$in": app_ids},
        "scheduled_at": {"$gte": now},
        "status": "scheduled"
    }).sort("scheduled_at", 1).limit(5)
    interviews = await cursor.to_list(length=5)
        
    if not interviews:
        await update.message.reply_text("📅 *No upcoming interviews scheduled.* Good luck in the search!", reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
        return
        
    response = "🗓️ *Upcoming Interviews:*\n\n"
    for idx, interview in enumerate(interviews, 1):
        app = app_map.get(interview["application_id"], {})
        company = app.get("company_name", "Unknown Company")
        title = app.get("job_title", "Unknown Role")
        
        scheduled_at = interview["scheduled_at"]
        formatted_time = scheduled_at.strftime("%b %d at %I:%M %p") if isinstance(scheduled_at, datetime) else str(scheduled_at)
        
        response += (
            f"{idx}. *{company}* — {title}\n"
            f"   Type: `{interview.get('round_type')}` (Round {interview.get('round_number')})\n"
            f"   Time: {formatted_time}\n"
            f"   Link/Loc: [Click here]({interview.get('location_or_link')}) if virtual\n\n"
        )
        
    await update.message.reply_text(response, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown", disable_web_page_preview=True)


async def followups_command(update: Update, context: CallbackContext):
    """Show pending followups."""
    if not await check_admin_permission(update):
        return
    chat_id = str(update.effective_chat.id)
    db = get_db_instance()
    
    user = await db.users.find_one({"telegram_chat_id": chat_id})
    if not user:
        await update.message.reply_text("⚠️ Account not linked. Use `/start` to connect your profile first.", reply_markup=MAIN_KEYBOARD)
        return
        
    apps = await db.applications.find({"user_id": user["_id"]}).to_list(length=1000)
    app_ids = [app["_id"] for app in apps]
    app_map = {app["_id"]: app for app in apps}

    cursor = db.follow_ups.find({
        "application_id": {"$in": app_ids},
        "status": "pending"
    }).sort("due_date", 1).limit(5)
    follow_ups = await cursor.to_list(length=5)
        
    if not follow_ups:
        await update.message.reply_text("✅ *No pending follow-up tasks!* You are completely up to date.", reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
        return
        
    response = "⏰ *Due/Pending Follow-Ups:*\n\n"
    for idx, followup in enumerate(follow_ups, 1):
        app = app_map.get(followup["application_id"], {})
        company = app.get("company_name", "Unknown Company")
        title = app.get("job_title", "Unknown Role")
        
        due_date = followup["due_date"]
        due_str = due_date.strftime("%Y-%m-%d") if isinstance(due_date, datetime) else str(due_date)[:10]
        
        response += (
            f"{idx}. *{company}* ({title})\n"
            f"   Due: `{due_str}`\n"
            f"   Task: {followup.get('notes') or 'Send follow-up message'}\n\n"
        )
        
    await update.message.reply_text(response, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")


async def handle_incoming_text(update: Update, context: CallbackContext):
    """Handle plain text sent by linked users. Try to parse as Job description if it looks like one."""
    if not await check_admin_permission(update):
        return
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text.strip()
    db = get_db_instance()
    
    user = await db.users.find_one({"telegram_chat_id": chat_id})
    if not user:
        await update.message.reply_text("⚠️ Account not linked. Use `/start` to connect your profile first.", reply_markup=MAIN_KEYBOARD)
        return
        
    if message_text == "📊 Stats":
        await stats_command(update, context)
    elif message_text == "📅 Interviews":
        await interviews_command(update, context)
    elif message_text == "⏰ Follow-ups":
        await followups_command(update, context)
    else:
        await update.message.reply_text(
            "🚫 *Direct text input is not allowed.* Please use the buttons below to interact with the bot:",
            reply_markup=MAIN_KEYBOARD,
            parse_mode="Markdown"
        )


def get_telegram_app() -> TelegramApp:
    """Initialize and retrieve the python-telegram-bot application."""
    global telegram_app
    if telegram_app is not None:
        return telegram_app

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bot features will not work.")
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not configured.")

    # Build the Application
    app = TelegramApp.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Add Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("interviews", interviews_command))
    app.add_handler(CommandHandler("followups", followups_command))

    # Add Message Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_text))

    telegram_app = app
    logger.info("Telegram Bot Application initialized successfully.")
    return telegram_app


async def init_telegram_bot():
    """Startup routine to initialize the bot and start polling in development."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram token is not set. Skipping Telegram Bot startup.")
        return

    try:
        app = get_telegram_app()
        await app.initialize()
        await app.start()
        if app.updater:
            await app.updater.start_polling()
        logger.info("Telegram bot started successfully and polling active.")
    except Exception as e:
        logger.exception("Failed to initialize and start Telegram Bot: %s", e)


async def shutdown_telegram_bot():
    """Shutdown routine to stop the bot and release resources."""
    global telegram_app
    if telegram_app:
        try:
            if telegram_app.updater:
                await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
            logger.info("Telegram bot shut down successfully.")
        except Exception as e:
            logger.exception("Error during Telegram bot shutdown: %s", e)
