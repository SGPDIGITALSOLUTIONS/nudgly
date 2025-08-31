"""
Nudgly - Personal ADHD Reminder Assistant

A minimal WhatsApp-first reminder bot that helps manage daily tasks
through natural language voice notes and text messages.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import validate_settings
from .db import init_db
# Scheduler disabled for serverless deployment
# from .scheduler import start_scheduler, stop_scheduler
from .handlers import router as twilio_router
from .web import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Nudgly...")
    
    # Validate configuration
    try:
        validate_settings()
        print("✅ Settings validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        raise
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    # Scheduler disabled for serverless deployment
    print("⚠️ Scheduler disabled (serverless mode)")
    
    print("🎉 Nudgly is ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Nudgly...")
    print("✅ Serverless shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Nudgly",
    description="Personal ADHD Reminder Assistant - WhatsApp-first task management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for potential web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(web_router, tags=["Web"])
app.include_router(twilio_router, tags=["WhatsApp"])


# Remove this root endpoint as it's now handled by web router


@app.get("/status")
async def status():
    """Application status endpoint."""
    from .settings import TZ, DAILY_DIGEST_HOUR, ALLOWED_SENDERS
    
    return {
        "status": "running",
        "timezone": TZ,
        "daily_digest_hour": DAILY_DIGEST_HOUR,
        "allowed_senders_count": len(ALLOWED_SENDERS),
        "features": {
            "whatsapp_integration": True,
            "voice_transcription": True,
            "natural_language_parsing": True,
            "scheduled_reminders": True,
            "daily_digest": True
        }
    }


if __name__ == "__main__":
    # For development - use uvicorn app.main:app --reload for production
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


