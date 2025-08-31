"""Configuration settings for Nudgly application."""

import os
from typing import Set
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application settings
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
TZ = os.getenv("TZ", "UTC")
DAILY_DIGEST_HOUR = int(os.getenv("DAILY_DIGEST_HOUR", "8"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nudgly.db")

# Security - Allowed WhatsApp senders
ALLOWED_SENDERS: Set[str] = {
    s.strip() for s in os.getenv("ALLOWED_SENDERS", "").split(",") if s.strip()
}

# Twilio WhatsApp configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validation
def validate_settings():
    """Validate that required environment variables are set."""
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN", 
        "TWILIO_WHATSAPP_NUMBER",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    if not ALLOWED_SENDERS:
        print("Warning: No ALLOWED_SENDERS configured - all numbers will be blocked")

# Command patterns for natural language processing
REMINDER_KEYWORDS = [
    "reminder:", "remind me", "add", "schedule", "set reminder",
    "don't forget", "remember to", "task:", "todo:"
]

LIST_KEYWORDS = ["list", "show", "what's today", "today", "schedule"]
DONE_KEYWORDS = ["done", "complete", "completed", "finished", "tick off"]
CANCEL_KEYWORDS = ["cancel", "delete", "remove", "nevermind"]

