"""
Web interface routes for Nudgly dashboard.
"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .db import get_db
from .models import Reminder
from .settings import ALLOWED_SENDERS
from .parsers import parse_text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Simple session storage (in production, use Redis or database)
active_sessions = {}

def get_current_user(request: Request) -> Optional[str]:
    """Get current logged-in user from session."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]["phone"]
    return None

def require_auth(request: Request) -> str:
    """Require authentication, redirect to login if not authenticated."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root page - redirect to dashboard if logged in, otherwise show login."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Show login page."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })

@router.post("/login")
async def login(
    request: Request,
    phone: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    # Simple authentication - check if phone is in allowed senders
    # In production, use proper password hashing and user management
    if phone not in ALLOWED_SENDERS:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Phone number not authorized",
            "phone": phone
        })
    
    # For demo purposes, accept any password for allowed numbers
    # TODO: Implement proper password verification
    if not password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Password required",
            "phone": phone
        })
    
    # Create session
    import uuid
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "phone": phone,
        "created_at": datetime.utcnow()
    }
    
    # Set cookie and redirect
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=86400,  # 24 hours
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    return response

@router.get("/logout")
async def logout(request: Request):
    """Logout and clear session."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_id")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    user_phone = require_auth(request)
    
    today = date.today()
    now = datetime.now()
    
    # Get today's tasks
    today_tasks = db.query(Reminder).filter(
        and_(
            Reminder.for_user == user_phone,
            Reminder.status == "PENDING",
            Reminder.due_at.isnot(None),
            Reminder.due_at >= datetime.combine(today, datetime.min.time()),
            Reminder.due_at < datetime.combine(today, datetime.max.time())
        )
    ).order_by(Reminder.due_at).all()
    
    # Get upcoming tasks (beyond today)
    upcoming_tasks = db.query(Reminder).filter(
        and_(
            Reminder.for_user == user_phone,
            Reminder.status == "PENDING",
            or_(
                Reminder.due_at.is_(None),
                Reminder.due_at >= datetime.combine(today, datetime.max.time())
            )
        )
    ).order_by(Reminder.due_at.asc()).limit(10).all()
    
    # Get counts
    today_count = len(today_tasks)
    pending_count = db.query(Reminder).filter(
        and_(
            Reminder.for_user == user_phone,
            Reminder.status == "PENDING"
        )
    ).count()
    
    completed_today_count = db.query(Reminder).filter(
        and_(
            Reminder.for_user == user_phone,
            Reminder.status == "DONE",
            Reminder.updated_at >= datetime.combine(today, datetime.min.time())
        )
    ).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_phone": user_phone,
        "today_tasks": today_tasks,
        "upcoming_tasks": upcoming_tasks,
        "today_count": today_count,
        "pending_count": pending_count,
        "completed_today_count": completed_today_count
    })

@router.post("/api/add-task")
async def add_task(
    request: Request,
    db: Session = Depends(get_db)
):
    """API endpoint to add a new task."""
    user_phone = require_auth(request)
    
    data = await request.json()
    text = data.get("text", "").strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Task text required")
    
    # Parse the reminder using existing parser
    try:
        parsed = parse_text(text)
        
        reminder = Reminder(
            created_by=user_phone,
            for_user=user_phone,  # User creating for themselves
            text=parsed.text,
            due_at=parsed.due_at,
            status="PENDING",
            source="web"
        )
        
        db.add(reminder)
        db.commit()
        
        return {"status": "success", "message": "Task added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse reminder: {str(e)}")

@router.post("/api/task/{task_id}/done")
async def mark_task_done(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Mark a task as done."""
    user_phone = require_auth(request)
    
    task = db.query(Reminder).filter(
        and_(
            Reminder.id == task_id,
            Reminder.for_user == user_phone
        )
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "DONE"
    task.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": "Task marked as done"}

@router.post("/api/task/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Cancel a task."""
    user_phone = require_auth(request)
    
    task = db.query(Reminder).filter(
        and_(
            Reminder.id == task_id,
            Reminder.for_user == user_phone
        )
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "CANCELLED"
    task.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": "Task cancelled"}
