"""
Scheduler module for Nudgly - handles reminder notifications and daily digest.
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

from .db import engine
from .models import Reminder
from .settings import DAILY_DIGEST_HOUR, TZ, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
# Import moved to function to avoid circular import

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def send_reminder_notification(reminder_id: int):
    """Send a reminder notification via WhatsApp."""
    db = SessionLocal()
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder or reminder.status != "PENDING":
            logger.info(f"Reminder {reminder_id} not found or not pending, skipping")
            return
        
        message = f"🔔 Reminder: {reminder.text}"
        if reminder.due_at:
            message += f"\n⏰ Due: {reminder.due_at.strftime('%H:%M')}"
        
        # Send WhatsApp message - import locally to avoid circular import
        try:
            from twilio.rest import Client
            from .settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
            
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=reminder.for_user,
                body=message
            )
            success = True
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            success = False
        
        if success:
            logger.info(f"Reminder notification sent for reminder {reminder_id}")
        else:
            logger.error(f"Failed to send reminder notification for reminder {reminder_id}")
            
    except Exception as e:
        logger.error(f"Error sending reminder notification {reminder_id}: {e}")
    finally:
        db.close()

def send_daily_digest():
    """Send daily digest to all users with pending reminders."""
    db = SessionLocal()
    try:
        # Get all users with pending reminders for today
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Group reminders by user
        from sqlalchemy import func
        users_with_reminders = db.query(Reminder.for_user).filter(
            and_(
                Reminder.status == "PENDING",
                Reminder.due_at >= today_start,
                Reminder.due_at <= today_end
            )
        ).distinct().all()
        
        for (user_phone,) in users_with_reminders:
            # Get today's reminders for this user
            reminders = db.query(Reminder).filter(
                and_(
                    Reminder.for_user == user_phone,
                    Reminder.status == "PENDING",
                    Reminder.due_at >= today_start,
                    Reminder.due_at <= today_end
                )
            ).order_by(Reminder.due_at).all()
            
            if reminders:
                # Build digest message
                date_str = today.strftime('%A, %B %d')
                message = f"🗓 Daily Digest - {date_str}\n\n"
                
                for i, reminder in enumerate(reminders, 1):
                    time_str = reminder.due_at.strftime('%H:%M') if reminder.due_at else 'No time'
                    message += f"{i}. {reminder.text} - {time_str}\n"
                
                message += f"\n📱 Reply with DONE [number] to mark complete"
                message += f"\n💻 View all tasks: {reminder.for_user.replace('whatsapp:', '').replace('+', '')}"
                
                # Send digest - import locally to avoid circular import
                try:
                    from twilio.rest import Client
                    from .settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
                    
                    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                    client.messages.create(
                        from_=TWILIO_WHATSAPP_NUMBER,
                        to=user_phone,
                        body=message
                    )
                    success = True
                except Exception as e:
                    logger.error(f"Error sending WhatsApp message: {e}")
                    success = False
                
                if success:
                    logger.info(f"Daily digest sent to {user_phone}")
                else:
                    logger.error(f"Failed to send daily digest to {user_phone}")
                    
    except Exception as e:
        logger.error(f"Error sending daily digest: {e}")
    finally:
        db.close()

def schedule_reminder(reminder: Reminder):
    """Schedule a specific reminder notification."""
    if not reminder.due_at or not scheduler:
        return
    
    # Schedule notification 5 minutes before due time
    notification_time = reminder.due_at - timedelta(minutes=5)
    
    # Only schedule if notification time is in the future
    if notification_time > datetime.now():
        job_id = f"reminder_{reminder.id}"
        
        try:
            scheduler.add_job(
                send_reminder_notification,
                DateTrigger(run_date=notification_time),
                args=[reminder.id],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Scheduled reminder {reminder.id} for {notification_time}")
        except Exception as e:
            logger.error(f"Failed to schedule reminder {reminder.id}: {e}")

def start_scheduler():
    """Start the background scheduler."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler(timezone=TZ)
    
    # Schedule daily digest
    scheduler.add_job(
        send_daily_digest,
        CronTrigger(hour=DAILY_DIGEST_HOUR, minute=0, timezone=TZ),
        id="daily_digest",
        replace_existing=True
    )
    
    # Schedule existing pending reminders
    db = SessionLocal()
    try:
        pending_reminders = db.query(Reminder).filter(
            and_(
                Reminder.status == "PENDING",
                Reminder.due_at.isnot(None),
                Reminder.due_at > datetime.now()
            )
        ).all()
        
        for reminder in pending_reminders:
            schedule_reminder(reminder)
            
        logger.info(f"Scheduled {len(pending_reminders)} existing reminders")
        
    except Exception as e:
        logger.error(f"Error scheduling existing reminders: {e}")
    finally:
        db.close()
    
    scheduler.start()
    logger.info("Scheduler started successfully")

def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")

def get_scheduler():
    """Get the current scheduler instance."""
    return scheduler
