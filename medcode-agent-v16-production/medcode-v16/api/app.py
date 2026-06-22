"""
MedCode AI Agent - FastAPI Web Server (V19 HIPAA-Compliant)

Provides REST API for the secure deterministic healthcare pipeline.
- V19 HIPAA-compliant security middleware
- TLS/HTTPS enforcement
- Rate limiting
- Security headers
- PHI encryption at rest
- Tamper-evident audit logging
"""

import asyncio
import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.models import ClinicalNote, FinalCodeSet
from core.config import FORCE_HTTPS, RATE_LIMIT_RPM
from agents.orchestrator import AgentOrchestrator
from agents.workflow_controller import WorkflowControlledOrchestrator
from observability.metrics_collector import MetricsCollector
from observability.health_checker import HealthChecker
from security.tls_middleware import setup_security_middleware
from security.auth_middleware import AuthenticationMiddleware

app = FastAPI(title="MedCode AI Agent V19", version="19.0.0-hipaa")

# ── V19 Security Middleware ──────────────────────────────────────────────
setup_security_middleware(app, config={
    "force_https": FORCE_HTTPS,
    "rate_limit_rpm": RATE_LIMIT_RPM,
})
app.add_middleware(AuthenticationMiddleware)

# ── Observability singletons ────────────────────────────────────────────
# NOTE: must be created BEFORE importing route modules that share the name
# "health", to avoid the variable being shadowed by the module import.
metrics = MetricsCollector()
health_checker = HealthChecker()

# ── Register internal route modules ────────────────────────────────────
from api.routes import coding, debug, health as health_routes, history, search, timing
from api.routes.auth import router as auth_router
from api.routes.compliance import router as compliance_router
from api.routes.billing import router as billing_router
app.include_router(coding.router)
app.include_router(coding.v1_router)
app.include_router(debug.router)
app.include_router(health_routes.router)
app.include_router(health_routes.v1_router)
app.include_router(history.router)
app.include_router(history.v1_router)
app.include_router(search.router)
app.include_router(search.v1_router)
app.include_router(timing.router)
app.include_router(timing.v1_router)
app.include_router(auth_router)
app.include_router(compliance_router)
app.include_router(billing_router)

# ── Serve frontend static files ─────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the frontend HTML UI."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {
        "service": "MedCode AI Agent",
        "version": "19.0.0-hipaa",
        "status": "running",
        "hipaa_compliant": True,
        "security_features": [
            "PHI Encryption at Rest (Fernet AES-128)",
            "Tamper-Evident Audit Logs (Hash Chain)",
            "TLS/HTTPS Enforcement",
            "Rate Limiting",
            "Security Headers (HSTS, CSP, X-Frame-Options)",
            "JWT Authentication",
            "Automatic Session Logoff",
            "Emergency Access (Break-Glass)",
            "Minimum Necessary Access Controls",
        ],
        "architecture": (
            "HIPAA-Compliant | PHI-Encrypted | "
            "Audit-Logged | Evidence-Grounded | Enterprise Healthcare"
        ),
        "phases": [
            "Phase 1: Deterministic Workflow Engine",
            "Phase 2: LLM Gateway Enforcement",
            "Phase 3: Scoped Context Architecture",
            "Phase 4: Evidence Grounding",
            "Phase 5: Assertion + Temporal Reasoning",
            "Phase 6: Secure Retrieval Architecture",
            "Phase 7: Consensus + Adjudication",
            "Phase 8: Observability + Audit",
        ],
        "endpoints": {
            "/": "This index",
            "/health": "Health check",
            "/v1/health": "Health check (versioned)",
            "/ready": "K8s readiness probe",
            "/v1/ready": "K8s readiness probe (versioned)",
            "/live": "K8s liveness probe",
            "/v1/live": "K8s liveness probe (versioned)",
            "/code": "POST — Code a clinical note (17-stage pipeline)",
            "/v1/code": "POST — Code a clinical note (versioned)",
            "/api/code": "POST — Code via router (coding agent pipeline)",
            "/api/v1/code": "POST — Code via router (versioned)",
            "/api/batch": "POST — Batch code multiple notes",
            "/api/v1/batch": "POST — Batch code multiple notes (versioned)",
            "/api/health": "Router health check",
            "/api/v1/health": "Router health check (versioned)",
            "/api/stats": "Aggregated statistics",
            "/api/v1/stats": "Aggregated statistics (versioned)",
            "/api/history": "Session history",
            "/api/v1/history": "Session history (versioned)",
            "/api/search": "Semantic code search",
            "/api/v1/search": "Semantic code search (versioned)",
            "/api/validate/{code}": "Code validation",
            "/api/v1/validate/{code}": "Code validation (versioned)",
            "/api/hierarchy/{code}": "Hierarchy exploration",
            "/api/v1/hierarchy/{code}": "Hierarchy exploration (versioned)",
            "/api/map/{code}": "Cross-vocabulary mapping",
            "/api/v1/map/{code}": "Cross-vocabulary mapping (versioned)",
            "/api/suggest": "Autocomplete suggestions",
            "/api/v1/suggest": "Autocomplete suggestions (versioned)",
            "/api/session/{session_id}": "Session detail",
            "/api/v1/session/{session_id}": "Session detail (versioned)",
            "/api/feedback": "POST — Submit feedback",
            "/api/v1/feedback": "POST — Submit feedback (versioned)",
            "/pipeline/stages": "List V13 pipeline stages",
            "/v1/pipeline/stages": "List V13 pipeline stages (versioned)",
            "/metrics": "Prometheus metrics",
            "/v1/metrics": "Prometheus metrics (versioned)",
            "/metrics/json": "JSON metrics snapshot",
            "/v1/metrics/json": "JSON metrics snapshot (versioned)",
            "/audit/events": "Recent security events",
            "/v1/audit/events": "Recent security events (versioned)",
            "/docs": "Swagger UI",
        },
    }


class NoteRequest(BaseModel):
    note_id: str = "note-001"
    text: str
    encounter_type: str = "outpatient"
    specialty: str = ""


# ── Health ──────────────────────────────────────────────────────────────

@app.get("/health")
@app.get("/v1/health")
async def health_check():
    """Full system health check with component status."""
    return health_checker.check_all().to_dict()


@app.get("/ready")
@app.get("/v1/ready")
async def readiness():
    """Kubernetes readiness probe."""
    return {"status": "ready"} if health_checker.is_healthy() else {"status": "not_ready"}


@app.get("/live")
@app.get("/v1/live")
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


# ── Coding Pipeline ────────────────────────────────────────────────────

@app.post("/code", response_model=dict)
@app.post("/v1/code", response_model=dict)
async def code_note(request: NoteRequest):
    """Process a clinical note through the full 17-stage V13 deterministic pipeline.

    Uses WorkflowControlledOrchestrator (V12 deterministic workflow)
    with all 8 V13 phases active.
    """
    # Use app.state.orchestrator if available (set by main.py), else fall back
    orchestrator = getattr(app.state, "orchestrator", None)
    if orchestrator is None:
        orchestrator = WorkflowControlledOrchestrator()

    note = ClinicalNote(
        note_id=request.note_id,
        text=request.text,
        encounter_type=request.encounter_type,
        specialty=request.specialty,
    )
    try:
        result = await orchestrator.process_note(note)
        result_dict = result.to_dict()
        metrics.record_note_complete(
            is_accepted=not result.is_rejected,
            requires_review=result.requires_human_review,
            confidence=result_dict.get("confidence_overall", result_dict.get("confidence", 0)),
            processing_time_ms=result.processing_time_ms,
        )
        return result_dict
    except Exception as e:
        metrics.record_stage_failure("pipeline")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/stages")
@app.get("/v1/pipeline/stages")
async def pipeline_stages():
    """Return the full list of V13 pipeline stages."""
    return {
        "version": "13.0.0",
        "stages": [
            # Stage 0: Privacy & Security
            "privacy_deidentify",
            # Stage 1-2: Extraction
            "normalization",
            "extraction",
            # Stage 3: Assertion
            "assertion",
            # Stage 4-5: Evidence
            "evidence_grounding",
            "ontology_mapping",
            # Stage 6: Retrieval
            "retrieval",
            # Stage 7-8: Consensus
            "consensus",
            "candidate_generation",
            # Stage 9: Ontology Reasoning
            "ontology_reasoning",
            # Stage 10-11: Rules & Compliance
            "rule_engine",
            "compliance_validation",
            # Stage 12: Sequencing
            "sequencing",
            # Stage 13: Confidence
            "confidence_calibration",
            # Stage 14: Security Audit
            "security_audit",
            # Stage 15: Assembly
            "final_assembly",
            "complete",
        ],
        "description": "Secure evidence-grounded clinical reasoning pipeline with 17 stages",
    }


# ── Observability ──────────────────────────────────────────────────────

@app.get("/metrics")
@app.get("/v1/metrics")
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint."""
    return metrics.get_prometheus_text()


@app.get("/metrics/json")
@app.get("/v1/metrics/json")
async def metrics_json():
    """JSON-formatted metrics snapshot."""
    return metrics.get_metrics().to_dict()


@app.get("/metrics/reset")
@app.get("/v1/metrics/reset")
async def metrics_reset():
    """Reset all metrics counters (admin)."""
    metrics.reset()
    return {"status": "reset"}


# ── Audit ──────────────────────────────────────────────────────────────

@app.get("/audit/events")
@app.get("/v1/audit/events")
async def audit_events(limit: int = 50):
    """Get recent security events."""
    from audit.security_events import SecurityEventRegistry
    registry = SecurityEventRegistry()
    if hasattr(registry, "get_events"):
        events = registry.get_events(limit=limit)
    else:
        events = registry.summarize() if hasattr(registry, "summarize") else {}
    return {"events": events, "count": len(events) if isinstance(events, list) else 0}