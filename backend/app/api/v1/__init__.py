"""
TB Personal OS - API v1 Router
Main API router configuration
"""

from fastapi import APIRouter

# Import route modules
from app.api.v1.endpoints import (
    inbox, tasks, telegram, assistant,
    scheduler, checkins, google_auth, calendar, projects, gmail, drive,
    content, finance, memory, insights, autonomy, health, bookmarklet, leads, learning, modes,
    goals, reports, conversation
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(scheduler.router, tags=["scheduler"])
api_router.include_router(checkins.router, tags=["checkins"])
api_router.include_router(google_auth.router, tags=["google-auth"])
api_router.include_router(calendar.router, tags=["calendar"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(gmail.router, tags=["gmail"])
api_router.include_router(drive.router, tags=["drive"])
api_router.include_router(content.router, tags=["content"])
api_router.include_router(finance.router, tags=["finance"])
api_router.include_router(memory.router, tags=["memory"])
api_router.include_router(insights.router, tags=["insights"])
api_router.include_router(autonomy.router, tags=["autonomy"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(bookmarklet.router, tags=["bookmarklet"])
api_router.include_router(leads.router, tags=["leads"])
api_router.include_router(learning.router, tags=["learning"])
api_router.include_router(modes.router, tags=["modes"])
api_router.include_router(goals.router, tags=["goals"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(conversation.router, tags=["conversation"])


@api_router.get("/")
async def api_root():
    """API v1 root"""
    return {
        "message": "TB Personal OS API v1",
        "status": "operational",
        "endpoints": {
            "inbox": "/api/v1/inbox",
            "tasks": "/api/v1/tasks",
            "telegram": "/api/v1/telegram",
            "assistant": "/api/v1/assistant",
            "scheduler": "/api/v1/scheduler",
            "checkins": "/api/v1/checkins",
            "google_auth": "/api/v1/auth/google",
            "calendar": "/api/v1/calendar",
            "projects": "/api/v1/projects",
            "gmail": "/api/v1/gmail",
            "drive": "/api/v1/drive",
            "content": "/api/v1/content",
            "finance": "/api/v1/finance",
            "memory": "/api/v1/memory",
            "insights": "/api/v1/insights",
            "autonomy": "/api/v1/autonomy",
            "health": "/api/v1/health",
            "bookmarklet": "/api/v1/bookmarklet",
            "leads": "/api/v1/leads",
            "learning": "/api/v1/learning",
            "modes": "/api/v1/modes",
            "goals": "/api/v1/goals",
            "reports": "/api/v1/reports",
            "conversation": "/api/v1/conversation",
        }
    }
