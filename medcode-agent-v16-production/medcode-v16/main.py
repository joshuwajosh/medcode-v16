"""
MedCode AI Agent v13 — FastAPI Entrypoint
==========================================
Secure | Deterministic | Evidence-Grounded | Privacy-Preserving | Audit-Safe

All 8 V13 phases active:
  Phase 1 — Deterministic Workflow Engine
  Phase 2 — Mandatory LLM Gateway Enforcement
  Phase 3 — Scoped Context Architecture
  Phase 4 — Evidence Grounding
  Phase 5 — Assertion + Temporal Reasoning
  Phase 6 — Secure Retrieval Architecture
  Phase 7 — Consensus + Adjudication
  Phase 8 — Observability + Audit

Usage:
    uvicorn main:app --reload
    uvicorn main:app --reload --log-level debug
    python main.py              # runs via uvicorn programmatically
"""

import sys
import os
import time
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import APP_PORT, APP_HOST, LOG_LEVEL

# ── Structured Logging Setup ────────────────────────────────────────
from security.logging_setup import setup_logging
setup_logging(log_level=LOG_LEVEL)

# ── Import the main app from api.app (routers already registered there) ──
from api.app import app

# ── Request/Response Logging Middleware ──────────────────────────────
from security.request_logger import RequestLoggerMiddleware
app.add_middleware(RequestLoggerMiddleware)

# ── Input Sanitization Middleware ────────────────────────────────────
from security.sanitization_middleware import SanitizationMiddleware
app.add_middleware(SanitizationMiddleware)


# Note: Root endpoint (`GET /`) is registered in api/app.py as serve_index().
# It serves the frontend HTML when api/static/index.html exists, or returns
# a JSON response with service info, phases, and all endpoints otherwise.


# ── Print registered routes on startup ───────────────────────────────
@app.on_event("startup")
async def startup():
    """Initialize app state on startup."""
    from storage.database import Database
    from agents.workflow_controller import WorkflowControlledOrchestrator

    # Initialize database
    app.state.db = Database()
    app.state.start_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # Initialize V12 deterministic orchestrator
    app.state.orchestrator = WorkflowControlledOrchestrator()

    # Initialize searcher and omop (placeholder — real OMOP needs API key)
    app.state.searcher = None
    app.state.omop = None

    # Print registered routes
    print(f"\n{'='*60}")
    print(f"  MedCode AI Agent v13 — Server Starting")
    print(f"{'='*60}")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ",".join(sorted(route.methods - {"HEAD", "OPTIONS"}))
            if methods:
                print(f"    {methods:8s} {route.path}")
    print(f"{'='*60}")
    print(f"  Docs:  http://{APP_HOST}:{APP_PORT}/docs")
    print(f"  Root:  http://{APP_HOST}:{APP_PORT}/")
    print(f"  Health: http://{APP_HOST}:{APP_PORT}/health")
    print(f"{'='*60}\n")


# ── Direct execution ─────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )
