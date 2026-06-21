"""
MedCode AI Agent v13 — Coding Routes
======================================
POST /api/code   — Code a single clinical note via V12 deterministic workflow
POST /api/batch  — Batch code multiple notes
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.models import ClinicalNote, FinalCodeSet
from storage.database import Database
from utils.logging_utils import get_logger

logger = get_logger()

router = APIRouter(prefix="/api", tags=["coding"])
v1_router = APIRouter(prefix="/api/v1", tags=["coding"])


# ── V15 Pipeline Models ────────────────────────────────────────────────

class V15CodeRequest(BaseModel):
    note: str
    mdm_level: str = "moderate"
    systems: List[str] = ["ICD10CM", "CPT"]
    session_id: str = ""
    cpc_mode: bool = False
    force_cpt_only: bool = False

    class Config:
        max_text_length = 50000


class V15BatchCodeRequest(BaseModel):
    notes: List[str]
    mdm_level: str = "moderate"
    systems: List[str] = ["ICD10CM", "CPT"]
    cpc_mode: bool = False


# ── V15 Pipeline Instance ───────────────────────────────────────────────

def get_v15_pipeline(request: Request):
    """Get or create a V15 pipeline instance."""
    pipeline = getattr(request.app.state, "v15_pipeline", None)
    if pipeline is None:
        from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15 as V15Pipeline
        pipeline = V15Pipeline()
        request.app.state.v15_pipeline = pipeline
    return pipeline


# ── V15 API Endpoints ───────────────────────────────────────────────────

@router.post("/v15/code", tags=["coding"])
async def v15_code_note(request: Request, body: V15CodeRequest):
    """
    Code a clinical note through the V15 CPC-exam-level reasoning pipeline.

    Features:
      - Document Classification (13 types)
      - CPC Question Detection (Phase 3)
      - Procedure-First Detection (Phase 2)
      - Evidence Extraction V2
      - Specialty Routing V2 (18 specialties)
      - Cardiac Surgery CPT Engine (Phase 4)
      - Breast Surgery CPT Engine (Phase 5)
      - Procedure Extraction
      - Specialty-Gated ICD Validation
      - CPT-First Surgical Workflow
      - CPC-Style Reasoning Engine
      - ICD Fallback Prevention (Phase 10)
      - Confidence Safety System (0.75 threshold)
      - Stage Logging
      - Reasoning Trace (Phase 6)
      - Audit Trail with Full Provenance
      - Debug Panel
    """
    if not body.note or len(body.note.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Clinical note must be at least 10 characters",
        )

    pipeline = get_v15_pipeline(request)
    session_id = body.session_id or str(uuid.uuid4())

    try:
        result = pipeline.run(
            note_text=body.note,
            note_id=session_id,
            mdm_level=body.mdm_level,
            is_cpc_exam=body.cpc_mode,
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"V15 coding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v15/cpc", tags=["coding"])
async def v15_cpc_code_note(request: Request, body: V15CodeRequest):
    """
    CPC-exam-specific coding endpoint.
    Activates procedure-first mode, CPC question detection, and full reasoning trace.
    Returns CPT codes with reasoning steps visible.
    """
    if not body.note or len(body.note.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Clinical note must be at least 10 characters",
        )

    pipeline = get_v15_pipeline(request)
    session_id = body.session_id or str(uuid.uuid4())

    try:
        result = pipeline.run(
            note_text=body.note,
            note_id=session_id,
            mdm_level=body.mdm_level,
            is_cpc_exam=True,
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"V15 CPC coding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v15/batch", tags=["coding"])
async def v15_batch_code(request: Request, body: V15BatchCodeRequest):
    """Code multiple notes through the V15 pipeline."""
    if not body.notes:
        raise HTTPException(status_code=400, detail="No notes provided")
    if len(body.notes) > 25:
        raise HTTPException(status_code=400, detail="Max 25 notes per batch")

    pipeline = get_v15_pipeline(request)
    try:
        results = []
        for note in body.notes:
            result = pipeline.run(
                note_text=note,
                note_id=str(uuid.uuid4()),
                mdm_level=body.mdm_level,
                is_cpc_exam=body.cpc_mode,
            )
            results.append(result)
        return {
            "results": [r.to_dict() for r in results],
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"V15 batch coding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v15/pipeline/stages", tags=["coding"])
async def v15_pipeline_stages():
    """Return the full list of V15 pipeline stages."""
    return {
        "version": "15.0.0",
        "pipeline": "V15 CPC-Exam-Level Medical Coding Pipeline",
        "stages": [
            "Stage 1: Document Classification Engine",
            "Stage 2: CPC Question Detection (Phase 3)",
            "Stage 3: Procedure-First Detection (Phase 2)",
            "Stage 4: Evidence Extraction V2",
            "Stage 5: Specialty Routing V2",
            "Stage 6: Procedure Extraction",
            "Stage 7: Cardiac Surgery CPT Engine (Phase 4)",
            "Stage 8: Breast Surgery CPT Engine (Phase 5)",
            "Stage 9: Specialty-Gated ICD Validation",
            "Stage 10: CPT Candidate Generation",
            "Stage 11: ICD Fallback Prevention (Phase 10)",
            "Stage 12: Confidence Safety System",
            "Stage 13: Audit Trail Assembly",
            "Stage 14: Reasoning Trace (Phase 6)",
            "Stage 15: Debug Panel Data (Phase 9)",
            "Stage 16: Final Assembly",
        ],
        "keyword_concept_cpt": "Keyword → Concept → Procedure Family → Coding Rule → CPT (Phase 7)",
        "reasoning_trace": "Step 1-6 visible for every CPC answer (Phase 6)",
        "hallucination_prevention": [
            "evidence_count > 0 required for every final code",
            "ICD fallback prevention (Phase 10)",
            "specialty_match validation",
            "evidence linkage verification",
        ],
        "confidence_threshold": 0.75,
        "supported_procedures": [
            "CABG (1-4 arterial grafts, vein grafts, re-do)",
            "Valve surgery (aortic, mitral, tricuspid, pulmonic)",
            "Aortic surgery (root, ascending, arch)",
            "Breast surgery (biopsy, lumpectomy, mastectomy)",
            "Congenital cardiac surgery",
            "General surgery (wound repair, I&D, excision, fracture)",
        ],
        "supported_specialties": [
            "Trauma", "Emergency Medicine", "Internal Medicine",
            "Family Medicine", "Cardiology", "Pulmonology", "Neurology",
            "Orthopedics", "Dermatology", "General Surgery",
            "Neurosurgery", "Gastroenterology", "Infectious Disease",
            "Psychiatry", "Pediatrics", "Oncology", "Urology",
            "Endocrinology",
        ],
    }


class CodeRequest(BaseModel):
    note: str
    mode: str = "balanced"
    systems: list[str] = ["ICD10CM", "CPT"]
    fast: bool = False
    session_id: str = ""


class BatchCodeRequest(BaseModel):
    notes: list[str]
    mode: str = "quick"
    systems: list[str] = ["ICD10CM", "CPT"]


def get_orchestrator(request: Request):
    """Get the V12 deterministic orchestrator from app state."""
    from agents.workflow_controller import WorkflowControlledOrchestrator
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        orch = WorkflowControlledOrchestrator()
    return orch


def get_db(request: Request) -> Database:
    """Get database from app state."""
    return request.app.state.db


@router.post("/code")
@v1_router.post("/code")
async def code_note(request: Request, body: CodeRequest):
    """
    Code a single clinical note through the V12 deterministic workflow.

    Supports SSE streaming if Accept: text/event-stream.
    Otherwise returns JSON FinalCodeSet with all 8 V13 phases active.
    """
    if not body.note or len(body.note.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Clinical note must be at least 10 characters",
        )

    # Check for SSE
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        return StreamingResponse(
            _stream_code(request, body),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Standard JSON response: use the deterministic CPT-first pipeline.
    db = get_db(request)

    session_id = body.session_id or str(uuid.uuid4())
    db.save_session(session_id, body.note, "clinical", body.mode, "processing")

    try:
        from agents.medcode_deterministic_pipeline import MedCodeDeterministicPipeline

        pipeline = getattr(request.app.state, "deterministic_pipeline", None)
        if pipeline is None:
            pipeline = MedCodeDeterministicPipeline()
            request.app.state.deterministic_pipeline = pipeline

        result = pipeline.run(
            note_text=body.note,
            note_id=session_id,
            mdm_level=body.mode,
        )

        result_dict = result.to_dict()

        # Save results to DB using V16 native fields
        all_results = []
        icd10_codes = result_dict.get("icd10_codes", [])
        cpt_codes = result_dict.get("cpt_codes", [])
        for i, c in enumerate(icd10_codes):
            all_results.append({
                **c,
                "code_type": "primary_dx" if i == 0 else "secondary_dx",
                "confidence_level": _confidence_level(c.get("confidence", 0)),
            })
        for c in cpt_codes:
            all_results.append({
                **c,
                "code_type": "procedure",
                "confidence_level": _confidence_level(c.get("confidence", 0)),
            })
        if all_results:
            db.save_results(session_id, all_results)

        db.update_session(
            session_id,
            status="complete",
            processing_time_s=result_dict.get("processing_time_ms", 0) / 1000,
            confidence_overall=result_dict.get("confidence", 0),
            needs_human_review=1 if result_dict.get("confidence", 1.0) < 0.40 else 0,
        )

        return result_dict

    except Exception as e:
        logger.error(f"Coding error: {e}")
        db.update_session(session_id, status="error")
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_code(request: Request, body: CodeRequest):
    """Stream coding progress via Server-Sent Events through all V12 workflow states."""
    import asyncio

    orchestrator = get_orchestrator(request)
    db = get_db(request)
    session_id = body.session_id or str(uuid.uuid4())

    yield "data: " + json.dumps({
        "event": "start",
        "mode": body.mode,
        "session_id": session_id,
        "v12_workflow": True,
    }) + "\n\n"

    # Emit V12 workflow states
    workflow_states = [
        "NOTE_RECEIVED",
        "PHI_SANITIZED",
        "EVIDENCE_EXTRACTED",
        "ASSERTION_VALIDATED",
        "ONTOLOGY_MAPPED",
        "RETRIEVAL_COMPLETED",
        "CANDIDATES_GENERATED",
        "COMPLIANCE_VALIDATED",
        "CONSENSUS_APPROVED",
        "AUDIT_ARCHIVED",
        "FINALIZED",
    ]

    for state in workflow_states:
        yield "data: " + json.dumps({
            "event": "workflow_state",
            "state": state,
            "status": "pending",
        }) + "\n\n"

    note = ClinicalNote(
        note_id=session_id,
        text=body.note,
        encounter_type=body.mode,
    )
    db.save_session(session_id, body.note, "clinical", body.mode, "processing")

    try:
        # Emit NOTE_RECEIVED → running
        yield "data: " + json.dumps({
            "event": "workflow_state",
            "state": "NOTE_RECEIVED",
            "status": "running",
        }) + "\n\n"

        loop = asyncio.get_event_loop()
        result_holder = {}

        async def run_pipeline():
            result = await orchestrator.process_note(note)
            result_holder["result"] = result

        task = asyncio.ensure_future(run_pipeline())

        # Stream workflow state updates while pipeline runs
        state_idx = 1
        while not task.done():
            await asyncio.sleep(1.5)
            if not task.done() and state_idx < len(workflow_states):
                yield "data: " + json.dumps({
                    "event": "workflow_state",
                    "state": workflow_states[state_idx],
                    "status": "running",
                }) + "\n\n"
                state_idx += 1

        await task

        result = result_holder.get("result")
        if result is None:
            raise RuntimeError("Pipeline returned no result")

        # Mark all states complete if pipeline succeeded
        for state in workflow_states:
            yield "data: " + json.dumps({
                "event": "workflow_state",
                "state": state,
                "status": "complete",
            }) + "\n\n"

        # Save to DB — streaming uses FinalCodeSet (legacy orchestrator path)
        result_dict = result.to_dict()
        all_results = []
        if result_dict.get("primary_dx"):
            all_results.append({
                **result_dict["primary_dx"],
                "code_type": "primary_dx",
                "confidence_level": _confidence_level(result_dict["primary_dx"].get("confidence", 0)),
            })
        for c in result_dict.get("secondary_dx", []):
            all_results.append({
                **c,
                "code_type": "secondary_dx",
                "confidence_level": _confidence_level(c.get("confidence", 0)),
            })
        if all_results:
            db.save_results(session_id, all_results)

        db.update_session(
            session_id,
            status="complete",
            processing_time_s=result_dict.get("processing_time_s", result_dict.get("processing_time_ms", 0) / 1000),
            confidence_overall=result_dict.get("confidence_overall", result_dict.get("confidence", 0)),
            needs_human_review=1 if result_dict.get("requires_human_review", result_dict.get("is_rejected", False)) else 0,
        )

        yield "data: " + json.dumps({
            "event": "complete",
            "result": result_dict,
        }) + "\n\n"

    except Exception as e:
        for state in workflow_states:
            yield "data: " + json.dumps({
                "event": "workflow_state",
                "state": state,
                "status": "error",
            }) + "\n\n"
        db.update_session(session_id, status="error")
        yield "data: " + json.dumps({
            "event": "error",
            "error": str(e),
        }) + "\n\n"

    yield "data: [DONE]\n\n"


@router.post("/batch")
@v1_router.post("/batch")
async def batch_code(request: Request, body: BatchCodeRequest):
    """Code multiple clinical notes in batch mode through V12 deterministic workflow."""
    if not body.notes:
        raise HTTPException(status_code=400, detail="No notes provided")
    if len(body.notes) > 25:
        raise HTTPException(status_code=400, detail="Max 25 notes per batch")

    orchestrator = get_orchestrator(request)
    db = get_db(request)

    notes = [
        ClinicalNote(
            note_id=str(uuid.uuid4()),
            text=n,
            encounter_type=body.mode,
        )
        for n in body.notes
    ]

    try:
        results = []
        for note in notes:
            result = await orchestrator.process_note(note)
            results.append(result)

            # Save batch results
            session_id = note.note_id
            db.save_session(
                session_id, note.text, "clinical", body.mode, "complete"
            )
            result_dict = result.to_dict()
            all_results = []
            if result_dict.get("primary_dx"):
                all_results.append({
                    **result_dict["primary_dx"],
                    "code_type": "primary_dx",
                })
            for c in result_dict.get("secondary_dx", []):
                all_results.append({
                    **c,
                    "code_type": "secondary_dx",
                })
            if all_results:
                db.save_results(session_id, all_results)

        return {
            "results": [r.to_dict() for r in results],
            "count": len(results),
        }

    except Exception as e:
        logger.error(f"Batch coding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _confidence_level(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    elif score >= 0.60:
        return "MED"
    return "LOW"


# ── V15 Direct Route (Phase 11 — enforced contract schema) ─────────────────

class V15DirectRequest(BaseModel):
    note: str
    session_id: str = ""
    mdm_level: str = "moderate"

    class Config:
        max_text_length = 50000


@router.post("/v15/direct", tags=["coding"])
@v1_router.post("/v15/direct", tags=["coding"])
async def v15_direct_code(request: Request, body: V15DirectRequest):
    """
    Phase 11 compliant endpoint. Returns the enforced contract schema:
    session_id, confidence, cpt_codes, icd10_codes, validation, audit,
    reasoning_trace, specialty, procedure_family, processing_time_ms, denial_risk.
    """
    if not body.note or len(body.note.strip()) < 10:
        raise HTTPException(status_code=400, detail="Clinical note must be at least 10 characters")

    from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15
    pipeline = getattr(request.app.state, "v15_direct_pipeline", None)
    if pipeline is None:
        pipeline = MedcodeDeterministicPipelineV15()
        request.app.state.v15_direct_pipeline = pipeline

    session_id = body.session_id or str(uuid.uuid4())
    result = pipeline.run(
        note_text=body.note,
        note_id=session_id,
        mdm_level=body.mdm_level,
    )
    return result.to_dict()


# ── V16 Enterprise Routes ─────────────────────────────────────────────────

class V16CodeRequest(BaseModel):
    note: str
    session_id: str = ""
    mdm_level: str = "moderate"
    encounter_type: str = "outpatient"


@router.post("/v16/code", tags=["v16"])
@v1_router.post("/v16/code", tags=["v16"])
async def v16_code_note(request: Request, body: V16CodeRequest):
    """
    V16 Enterprise endpoint.

    Returns full V16 schema including:
    - context_analysis (negation/historical/family/suspected/postop classification)
    - modifier_decisions (per-CPT modifier reasoning with NCCI/MUE/laterality/global period)
    - em_coding (MDM-based E/M level with explainable scoring)
    - documentation_quality (documentation_gaps[], score)
    - physician_queries (AHIMA-compliant clarification queries)
    - medical_necessity (per-CPT necessity score and denial risk)
    - full_audit_trace (every decision with source, rule, confidence)
    """
    if not body.note or len(body.note.strip()) < 10:
        raise HTTPException(status_code=422, detail="Clinical note must be at least 10 characters")

    from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV16
    pipeline = getattr(request.app.state, "v16_pipeline", None)
    if pipeline is None:
        pipeline = MedcodeDeterministicPipelineV16()
        request.app.state.v16_pipeline = pipeline

    session_id = body.session_id or str(uuid.uuid4())
    result = pipeline.run(
        note_text=body.note,
        note_id=session_id,
        mdm_level=body.mdm_level,
    )
    return result.to_dict()


@router.get("/v16/health", tags=["v16"])
async def v16_health():
    """V16 engine health check."""
    return {
        "version": "16.0.0",
        "engines": [
            "context_classifier", "modifier_engine", "em_engine",
            "documentation_quality", "physician_query", "medical_necessity",
            "global_period_validator_v16", "full_audit_trace",
        ],
        "status": "ok",
    }


# ── V19 HIPAA-Compliant Endpoint ──────────────────────────────────────────

class V19CodeRequest(BaseModel):
    """V19 HIPAA-compliant coding request with strict validation."""
    note: str
    session_id: str = ""
    mdm_level: str = "moderate"
    encounter_type: str = "outpatient"

    class Config:
        max_text_length = 50000
        json_schema_extra = {
            "example": {
                "note": "Patient presents with chest pain...",
                "mdm_level": "moderate",
            }
        }


@router.post("/v19/code", tags=["v19"])
@v1_router.post("/v19/code", tags=["v19"])
async def v19_code_note(request: Request, body: V19CodeRequest):
    """
    V19 HIPAA-compliant coding endpoint.

    Security Features:
      - PHI encrypted at rest (Fernet AES-128)
      - All access audit-logged with tamper-evident hash chain
      - Rate limited per-IP
      - Input size validated (max 50,000 chars)
      - Authentication required (JWT Bearer token)
    
    Pipeline Stages:
      1. PHI Sanitization & Encryption
      2. Authentication Verification
      3. Fast Specialty Routing (V18)
      4. Evidence Extraction (V14)
      5. Specialty Reasoning (V17)
      6. Validation Suite (NCCI/MUE/LCD/NCD)
      7. Confidence Scoring (V15)
      8. Denial Prevention (V15)
      9. Audit Logging
      10. Output Filtering
    """
    from agents.v19_pipeline import get_v19_pipeline

    if not body.note or len(body.note.strip()) < 10:
        raise HTTPException(status_code=422, detail="Clinical note must be at least 10 characters")
    if len(body.note) > 50000:
        raise HTTPException(status_code=413, detail="Clinical note exceeds 50,000 character limit")

    user_id = getattr(request.state, "user_id", "api_user")
    session_id = body.session_id or str(uuid.uuid4())

    pipeline = get_v19_pipeline()
    result = pipeline.run(
        note_text=body.note,
        note_id=session_id,
        user_id=user_id,
        mdm_level=body.mdm_level,
        is_cpc_exam=body.encounter_type == "cpc",
    )

    return result.to_dict()
