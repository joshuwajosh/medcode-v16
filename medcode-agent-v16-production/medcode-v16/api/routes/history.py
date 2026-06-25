"""
MedCode AI Agent -- History & Feedback Routes
===============================================
GET  /api/history -- Session history
GET  /api/session/{id} -- Session detail
POST /api/feedback -- User feedback on coded results
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from utils.logging_utils import get_logger

logger = get_logger()
router = APIRouter(prefix="/api", tags=["history"])
v1_router = APIRouter(prefix="/api/v1", tags=["history"])


class FeedbackRequest(BaseModel):
    session_id: str
    code: str
    action: str  # accepted, rejected, corrected
    corrected_code: Optional[str] = None


def get_db(request: Request):
    return request.app.state.db


@router.get("/history")
@v1_router.get("/history")
async def get_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get recent coding session history."""
    db = get_db(request)
    try:
        sessions = db.get_history(limit=limit, offset=offset)
        return {"sessions": sessions, "count": len(sessions), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
@v1_router.get("/session/{session_id}")
async def get_session(
    request: Request,
    session_id: str,
):
    """Get a specific coding session with results."""
    db = get_db(request)
    try:
        session = db.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
@v1_router.post("/feedback")
async def submit_feedback(request: Request, body: FeedbackRequest):
    """Submit user feedback on a coded result."""
    if body.action not in ("accepted", "rejected", "corrected"):
        raise HTTPException(status_code=400, detail="Action must be: accepted, rejected, or corrected")
    if body.action == "corrected" and not body.corrected_code:
        raise HTTPException(status_code=400, detail="corrected_code required when action=corrected")

    db = get_db(request)
    try:
        db.save_feedback(
            session_id=body.session_id,
            code=body.code,
            action=body.action,
            corrected_code=body.corrected_code,
        )
        return {"status": "ok", "message": "Feedback saved"}
    except Exception as e:
        import sqlite3
        if isinstance(e, sqlite3.IntegrityError) and "FOREIGN KEY" in str(e):
            raise HTTPException(
                status_code=404,
                detail=f"Session '{body.session_id}' not found — create a coding session first",
            )
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
