"""WhatsApp webhook handlers and message processing."""

import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from sqlalchemy.orm import Session

from .settings import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER,
    ALLOWED_SENDERS, TZ
)
from .models import Reminder, ReminderStatus, ReminderSource
from .db import get_db
from .parsers import parse_text, ParsedReminder
from .whisper_utils import transcribe_if_voice
# Removed circular import - will handle scheduling differently
import pytz

router = APIRouter()

# Initialize Twilio client and validator
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio_validator = RequestValidator(TWILIO_AUTH_TOKEN)
timezone = pytz.timezone(TZ)


class MessageHandler:
    """Handles different types of WhatsApp messages."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def handle_reminder(self, parsed: ParsedReminder, from_phone: str, source: ReminderSource) -> str:
        """Handle a new reminder message."""
        if not parsed.due_at:
            return "❌ Sorry, I couldn't understand when you want to be reminded. Please try again with a specific time."
        
        # Create new reminder
        reminder = Reminder(
            created_by=from_phone,
            for_user=from_phone,  # For now, assume reminders are for the sender
            text=parsed.text,
            due_at=parsed.due_at.astimezone(pytz.UTC),
            status=ReminderStatus.PENDING,
            source=source
        )
        
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        
        # Scheduling handled in scheduler module to avoid circular imports
        
        # Format response
        due_local = parsed.due_at.astimezone(timezone)
        if due_local.date() == datetime.now(timezone).date():
            when_str = f"Today {due_local.strftime('%H:%M')}"
        elif due_local.date() == (datetime.now(timezone).date().replace(day=datetime.now(timezone).day + 1)):
            when_str = f"Tomorrow {due_local.strftime('%H:%M')}"
        else:
            when_str = due_local.strftime('%a %d %b %H:%M')
        
        return f"✅ *Added reminder #{reminder.id}*\n\n\"{parsed.text}\"\n\n📅 {when_str}"
    
    def handle_list(self, parsed: ParsedReminder, from_phone: str) -> str:
        """Handle list reminders request."""
        message_lower = parsed.text.lower()
        
        if "all" in message_lower:
            # List all pending reminders
            reminders = self.db.query(Reminder).filter(
                Reminder.for_user == from_phone,
                Reminder.status == ReminderStatus.PENDING
            ).order_by(Reminder.due_at).all()
            title = "📋 *All Pending Reminders*"
        else:
            # List today's reminders
            today_start = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59)
            
            reminders = self.db.query(Reminder).filter(
                Reminder.for_user == from_phone,
                Reminder.status == ReminderStatus.PENDING,
                Reminder.due_at >= today_start.astimezone(pytz.UTC),
                Reminder.due_at <= today_end.astimezone(pytz.UTC)
            ).order_by(Reminder.due_at).all()
            title = "📋 *Today's Reminders*"
        
        if not reminders:
            return f"{title}\n\nNo reminders found! 🎉"
        
        message = f"{title}\n\n"
        for reminder in reminders:
            due_local = reminder.due_at.astimezone(timezone)
            time_str = due_local.strftime('%H:%M')
            message += f"#{reminder.id} {reminder.text} - {time_str}\n"
        
        message += f"\n💬 Reply *DONE #number* to mark complete"
        return message
    
    def handle_done(self, parsed: ParsedReminder, from_phone: str) -> str:
        """Handle marking reminder as done."""
        reminder = self._find_reminder(parsed.text, from_phone)
        
        if not reminder:
            return "❌ Reminder not found. Try *LIST* to see your reminders."
        
        if reminder.status != ReminderStatus.PENDING:
            return f"ℹ️ Reminder #{reminder.id} is already marked as {reminder.status.lower()}."
        
        # Mark as done
        reminder.status = ReminderStatus.DONE
        reminder.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Scheduler will handle cleanup automatically
        
        return f"✅ *Completed reminder #{reminder.id}*\n\n\"{reminder.text}\"\n\nWell done! 🎉"
    
    def handle_cancel(self, parsed: ParsedReminder, from_phone: str) -> str:
        """Handle cancelling a reminder."""
        reminder = self._find_reminder(parsed.text, from_phone)
        
        if not reminder:
            return "❌ Reminder not found. Try *LIST* to see your reminders."
        
        if reminder.status != ReminderStatus.PENDING:
            return f"ℹ️ Reminder #{reminder.id} is already {reminder.status.lower()}."
        
        # Mark as cancelled
        reminder.status = ReminderStatus.CANCELLED
        reminder.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Scheduler will handle cleanup automatically
        
        return f"❌ *Cancelled reminder #{reminder.id}*\n\n\"{reminder.text}\""
    
    def _find_reminder(self, text: str, from_phone: str) -> Optional[Reminder]:
        """Find a reminder by ID or text content."""
        # Try to extract ID from text like "DONE 123" or "DONE #123"
        id_match = re.search(r'#?(\d+)', text)
        if id_match:
            reminder_id = int(id_match.group(1))
            return self.db.query(Reminder).filter(
                Reminder.id == reminder_id,
                Reminder.for_user == from_phone,
                Reminder.status == ReminderStatus.PENDING
            ).first()
        
        # Try to find by partial text match
        clean_text = re.sub(r'\b(done|cancel|delete|remove)\b', '', text, flags=re.IGNORECASE).strip()
        if clean_text:
            return self.db.query(Reminder).filter(
                Reminder.for_user == from_phone,
                Reminder.status == ReminderStatus.PENDING,
                Reminder.text.ilike(f'%{clean_text}%')
            ).first()
        
        return None


@router.post("/twilio/whatsapp")
async def handle_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming WhatsApp messages from Twilio."""
    try:
        # Get form data
        form = await request.form()
        from_phone = form.get("From", "")
        body = form.get("Body", "")
        media_count = int(form.get("NumMedia", "0"))
        
        # Security: Check if sender is allowed
        if ALLOWED_SENDERS and from_phone not in ALLOWED_SENDERS:
            print(f"Blocked message from unauthorized sender: {from_phone}")
            return PlainTextResponse("", status_code=200)  # Return 200 to avoid retries
        
        # Handle voice notes
        source = ReminderSource.TEXT
        if media_count > 0:
            transcribed = await transcribe_if_voice(form)
            if transcribed != body:  # Transcription was successful
                body = transcribed
                source = ReminderSource.VOICE
        
        if not body.strip():
            send_whatsapp_message(from_phone, "🤔 I didn't receive any text. Please send me a reminder!")
            return PlainTextResponse("OK")
        
        # Parse the message
        parsed = parse_text(body)
        
        # Handle different command types
        handler = MessageHandler(db)
        
        if parsed.command_type == "reminder":
            response = handler.handle_reminder(parsed, from_phone, source)
        elif parsed.command_type == "list":
            response = handler.handle_list(parsed, from_phone)
        elif parsed.command_type == "done":
            response = handler.handle_done(parsed, from_phone)
        elif parsed.command_type == "cancel":
            response = handler.handle_cancel(parsed, from_phone)
        else:
            response = "🤔 I didn't understand that. Try:\n\n• *Remind me to [task] at [time]*\n• *LIST* - see today's reminders\n• *DONE #[number]* - mark complete"
        
        # Send response
        send_whatsapp_message(from_phone, response)
        
        return PlainTextResponse("OK")
        
    except Exception as e:
        print(f"Error handling WhatsApp message: {e}")
        # Don't send error to user, just log it
        return PlainTextResponse("ERROR", status_code=500)


def send_whatsapp_message(to_phone: str, message: str):
    """Send a WhatsApp message via Twilio."""
    try:
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_phone,
            body=message
        )
        print(f"Sent message to {to_phone}: {message[:50]}...")
    except Exception as e:
        print(f"Error sending WhatsApp message to {to_phone}: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "nudgly"}


@router.get("/")
async def root():
    """Root endpoint with basic info."""
    return {"message": "Nudgly - Personal ADHD Reminder Assistant", "version": "1.0"}


