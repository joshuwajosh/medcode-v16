"""
MedCode AI Agent — Debug Pipeline Endpoint
============================================
GET/POST /debug/pipeline  — Trace actual code assignment step by step.

Returns intermediate pipeline state at every stage:
  - specialty routing
  - document type classification
  - retrieved documents / evidence entities
  - candidate codes
  - selected code
  - confidence
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.models import ClinicalNote
from security.auth import get_auth_service

router = APIRouter(prefix="/debug", tags=["debug"])


def require_admin(request: Request) -> None:
    """Dependency: require admin role for all debug endpoints."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header with Bearer token required")
    token = auth_header[7:]
    auth = get_auth_service()
    payload = auth.validate_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required for debug endpoints")


class DebugPipelineRequest(BaseModel):
    note: str
    note_id: str = "debug-001"


def _safe_get(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get an attribute that may not exist."""
    return getattr(obj, attr, default) if obj is not None else default


def _safe_call(obj: Any, method: str, *args, **kwargs) -> Any:
    """Safely call a method that may not exist."""
    fn = getattr(obj, method, None)
    if fn is not None:
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None
    return None


def _to_dict_safe(obj: Any, default: Any = None) -> Any:
    """Safely call to_dict() on an object."""
    if obj is None:
        return default
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            return str(obj)
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_to_dict_safe(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_dict_safe(v) for k, v in obj.items()}
    return str(obj)


@router.post("/pipeline", dependencies=[Depends(require_admin)])
async def debug_pipeline(request: Request, body: DebugPipelineRequest):
    """
    Execute the full coding pipeline and return ALL intermediate states for debugging.

    This is the primary tool for tracing wrong-code bugs.
    Every stage's output is captured in the response.

    Response structure:
    {
      "note_id": "...",
      "note_text_preview": "...",
      "stages": {
        "evidence_extraction": { ... },
        "specialty_routing": { ... },
        "retrieval": { ... },
        "candidate_generation": { ... },
        "final_output": { ... }
      },
      "selected_code": { ... },
      "confidence": 0.0,
      "processing_time_ms": 0.0,
      "errors": []
    }
    """
    if not body.note or len(body.note.strip()) < 3:
        raise HTTPException(status_code=400, detail="Note text must be at least 3 characters")

    debug_info: Dict[str, Any] = {
        "note_id": body.note_id,
        "note_text_preview": body.note[:300],
        "note_text_length": len(body.note),
        "stages": {},
        "selected_code": None,
        "selected_code_description": "",
        "confidence": 0.0,
        "status": "unknown",
        "pipeline_stages": [],
        "requires_human_review": False,
        "is_rejected": False,
        "rejection_reason": "",
        "errors": [],
        "processing_time_ms": 0.0,
    }

    start = time.time()

    # ── STAGE 1: Evidence Extraction ─────────────────────────────────────
    try:
        from core.evidence_engine.extractor import EvidenceEngineExtractor
        extractor = EvidenceEngineExtractor()
        bundle = extractor.extract(body.note, note_id=body.note_id)
        bundle_dict = _to_dict_safe(bundle, {})
        debug_info["stages"]["evidence_extraction"] = {
            "total_entities": _safe_get(bundle, "total_entities", 0),
            "has_trauma": _safe_get(bundle, "has_trauma", False),
            "has_observation": _safe_get(bundle, "has_observation", False),
            "primary_domain": _safe_get(bundle, "primary_domain", "unspecified"),
            "extraction_confidence": _safe_get(bundle, "extraction_confidence", 0.0),
            "entities": bundle_dict.get("entities", []),
            "negated_terms": _safe_get(bundle, "negated_terms", []),
        }
    except ImportError as e:
        debug_info["errors"].append(f"Evidence extraction unavailable: {e}")
        debug_info["stages"]["evidence_extraction"] = {"error": str(e)}
    except Exception as e:
        debug_info["errors"].append(f"Evidence extraction failed: {e}")
        debug_info["stages"]["evidence_extraction"] = {"error": str(e)}

    # ── STAGE 2: Specialty Routing ───────────────────────────────────────
    try:
        from routing.specialty_router import HardSpecialtyRouter
        router_inst = HardSpecialtyRouter()
        route_result = router_inst.route(bundle)
        route_dict = _to_dict_safe(route_result, {})
        debug_info["stages"]["specialty_routing"] = {
            "specialty": _safe_get(route_result, "specialty", ""),
            "specialty_value": route_dict.get("specialty", _safe_get(route_result, "specialty", "")),
            "confidence": route_dict.get("confidence", 0.0),
            "is_trauma": route_dict.get("is_trauma", False),
            "is_observation": route_dict.get("is_observation", False),
            "routing_reason": route_dict.get("routing_reason", ""),
            "allowed_ontologies": route_dict.get("allowed_ontologies", []),
            "blocked_ontologies": route_dict.get("blocked_ontologies", []),
            "icd_chapter_restrictions": route_dict.get("icd_chapter_restrictions", []),
            "encounter_type": route_dict.get("encounter_type", "unspecified"),
        }
    except ImportError as e:
        debug_info["errors"].append(f"Specialty routing unavailable: {e}")
        debug_info["stages"]["specialty_routing"] = {"error": str(e)}
    except Exception as e:
        debug_info["errors"].append(f"Specialty routing failed: {e}")
        debug_info["stages"]["specialty_routing"] = {"error": str(e)}

    # ── STAGE 3: Legacy Evidence Extraction (orchestrator-level) ─────────
    try:
        from evidence.extractor import EvidenceExtractor
        legacy_extractor = EvidenceExtractor()
        spans = legacy_extractor.extract(body.note)
        debug_info["stages"]["legacy_evidence_extraction"] = {
            "span_count": len(spans) if spans else 0,
            "spans_preview": [
                {
                    "text": _safe_get(s, "text", str(s))[:80],
                    "confidence": _safe_get(s, "confidence", 0.0),
                    "entity_type": _safe_get(s, "entity_type", ""),
                    "section": _safe_get(s, "section", ""),
                }
                for s in (spans or [])[:15]
            ],
        }
        # Also try DX_TERM_MAP keyword matching
        text_lower = body.note.lower()
        matched_keywords = []
        try:
            from agents.orchestrator import DX_TERM_MAP
            for keyword, entry in DX_TERM_MAP.items():
                if keyword in text_lower:
                    matched_keywords.append({
                        "keyword": keyword,
                        "code": entry[0],
                        "description": entry[1],
                        "confidence": entry[2],
                        "type": entry[3],
                    })
        except ImportError:
            pass
        debug_info["stages"]["legacy_evidence_extraction"]["keyword_matches"] = matched_keywords[:20]
    except ImportError as e:
        debug_info["errors"].append(f"Legacy evidence extraction unavailable: {e}")
    except Exception as e:
        debug_info["errors"].append(f"Legacy evidence extraction failed: {e}")

    # ── STAGE 4: Hybrid Retrieval ────────────────────────────────────────
    try:
        from retrieval.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever()
        retrieval_result = retriever.retrieve(body.note, top_k=10)
        retrieval_dict = _to_dict_safe(retrieval_result, {})
        top_codes = []
        reranked = _safe_get(retrieval_result, "reranked_codes", None)
        if reranked:
            top_codes = [
                {"code": _safe_get(c, "code", str(c)), "score": _safe_get(c, "score", 0.0)}
                for c in reranked[:10]
            ]
        elif hasattr(retrieval_result, "bm25_results"):
            top_codes = [
                {"code": r[0], "score": r[1]}
                for r in retrieval_result.bm25_results[:5]
            ]
        bm25_results = []
        if hasattr(retrieval_result, "bm25_results"):
            bm25_results = [
                {"code": r[0], "score": r[1]} for r in retrieval_result.bm25_results[:10]
            ]
        debug_info["stages"]["retrieval"] = {
            "retriever_type": "HybridRetriever (BM25 + Ontology + Guidelines)",
            "bm25_candidates": _safe_get(retrieval_result, "bm25_results", []),
            "top_codes": top_codes,
            "bm25_results_count": len(bm25_results),
            "reranked_count": len(top_codes),
        }
    except ImportError as e:
        debug_info["errors"].append(f"Retrieval unavailable: {e}")
        debug_info["stages"]["retrieval"] = {"error": str(e)}
    except Exception as e:
        debug_info["errors"].append(f"Retrieval failed: {e}")
        debug_info["stages"]["retrieval"] = {"error": str(e)}

    # ── STAGE 5: Full Pipeline Execution ─────────────────────────────────
    try:
        from agents.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        note = ClinicalNote(
            note_id=body.note_id,
            text=body.note,
            encounter_type="outpatient",
        )
        result = await orchestrator.process_note(note)
        result_dict = _to_dict_safe(result, {})

        # Extract selected code info
        primary_dx = _safe_get(result, "primary_dx", None)
        secondary_dx = _safe_get(result, "secondary_dx", [])

        selected_code_info = None
        if primary_dx:
            selected_code_info = {
                "code": _safe_get(primary_dx, "code", ""),
                "description": _safe_get(primary_dx, "name", ""),
                "confidence": _safe_get(primary_dx, "confidence", 0.0),
                "rationale": _safe_get(primary_dx, "rationale", ""),
                "code_type": _safe_get(primary_dx, "code_type", "ICD-10-CM"),
                "evidence": _safe_get(primary_dx, "evidence", []),
            }

        candidate_codes = []
        if primary_dx:
            candidate_codes.append({
                "code": _safe_get(primary_dx, "code", ""),
                "description": _safe_get(primary_dx, "name", ""),
                "confidence": _safe_get(primary_dx, "confidence", 0.0),
                "type": "primary_dx",
            })
        for c in (secondary_dx or []):
            candidate_codes.append({
                "code": _safe_get(c, "code", ""),
                "description": _safe_get(c, "name", ""),
                "confidence": _safe_get(c, "confidence", 0.0),
                "type": "secondary_dx",
            })

        debug_info["stages"]["pipeline_execution"] = {
            "confidence_overall": _safe_get(result, "confidence_overall", 0.0),
            "confidence_label": _safe_get(result, "confidence_label_val", ""),
            "is_rejected": _safe_get(result, "is_rejected", False),
            "rejection_reason": _safe_get(result, "rejection_reason", ""),
            "requires_human_review": _safe_get(result, "requires_human_review", False),
            "human_review_reasons": _safe_get(result, "human_review_reasons", []),
            "pipeline_stages_completed": _safe_get(result, "pipeline_stages_completed", []),
            "rule_violations": [
                {
                    "type": _safe_get(v, "violation_type", "UNKNOWN"),
                    "description": _safe_get(v, "description", ""),
                    "severity": _safe_get(v, "severity", "MEDIUM"),
                    "code": _safe_get(v, "code", ""),
                }
                for v in (_safe_get(result, "rule_violations", []) or [])
            ],
            "suppressed_codes": [
                {
                    "code": _safe_get(s, "code", ""),
                    "reason": _safe_get(s, "suppression_reason", ""),
                }
                for s in (_safe_get(result, "suppressed_codes", []) or [])
            ],
            "evidence_items_count": len(_safe_get(result, "evidence_items", []) or []),
            "compliance_status": result_dict.get("compliance", {}).get("status", "UNKNOWN"),
            "processing_time_ms": _safe_get(result, "processing_time_ms", 0.0),
            "workflow_states": _safe_get(result, "workflow_states", []),
            "workflow_success": _safe_get(result, "workflow_success", True),
        }

        # Update top-level fields
        debug_info["selected_code"] = selected_code_info
        debug_info["selected_code_description"] = (
            _safe_get(primary_dx, "name", "") if primary_dx else ""
        )
        debug_info["confidence"] = _safe_get(result, "confidence_overall", 0.0)
        debug_info["status"] = "REJECTED" if _safe_get(result, "is_rejected", False) else "FINALIZED"
        debug_info["pipeline_stages"] = _safe_get(result, "pipeline_stages_completed", [])
        debug_info["requires_human_review"] = _safe_get(result, "requires_human_review", False)
        debug_info["is_rejected"] = _safe_get(result, "is_rejected", False)
        debug_info["rejection_reason"] = _safe_get(result, "rejection_reason", "")

        debug_info["stages"]["candidate_codes"] = candidate_codes

    except ImportError as e:
        debug_info["errors"].append(f"Pipeline execution unavailable: {e}")
        debug_info["stages"]["pipeline_execution"] = {"error": str(e)}
    except Exception as e:
        debug_info["errors"].append(f"Pipeline execution failed: {e}")
        debug_info["stages"]["pipeline_execution"] = {"error": str(e)}

    # ── STAGE 6: V14 Pipeline (optional, for additional trace data) ──────
    try:
        from agents.v14_pipeline import V14Pipeline
        v14 = V14Pipeline(include_trace=True)
        v14_result = v14.run(body.note, note_id=body.note_id)
        debug_info["stages"]["v14_pipeline"] = {
            "status": _safe_get(v14_result, "status", ""),
            "specialty": _safe_get(v14_result, "specialty", ""),
            "finalized": _safe_get(v14_result, "finalized", False),
            "icd_codes": _safe_get(v14_result, "icd_codes", []),
            "cpt_codes": _safe_get(v14_result, "cpt_codes", []),
            "pending_review_codes": _safe_get(v14_result, "pending_review_codes", []),
            "pipeline_version": _safe_get(v14_result, "pipeline_version", ""),
            "processing_time_ms": _safe_get(v14_result, "processing_time_ms", 0.0),
            "error": _safe_get(v14_result, "error", None),
        }
        # Include full evidence and routing summaries from V14
        ev_summary = _safe_get(v14_result, "evidence_summary", {})
        if ev_summary:
            debug_info["stages"]["v14_pipeline"]["evidence_summary"] = ev_summary
        rt_summary = _safe_get(v14_result, "routing_summary", {})
        if rt_summary:
            debug_info["stages"]["v14_pipeline"]["routing_summary"] = rt_summary
    except ImportError:
        pass  # V14 pipeline is optional
    except Exception as e:
        debug_info["errors"].append(f"V14 pipeline trace failed: {e}")

    # ── Top-level convenience fields ──────────────────────────────────────
    debug_info["retrieved_documents"] = debug_info.get("stages", {}).get("retrieval", {}).get("top_codes", [])
    debug_info["document_type"] = debug_info.get("stages", {}).get("specialty_routing", {}).get("encounter_type", "unknown")
    debug_info["specialty"] = debug_info.get("stages", {}).get("specialty_routing", {}).get("specialty_value", "unknown")

    # ── Summary ───────────────────────────────────────────────────────────
    debug_info["processing_time_ms"] = round((time.time() - start) * 1000, 2)

    # Add diagnostic summary at the top for quick scanning
    selected_code_str = "NONE"
    if debug_info["selected_code"] and debug_info["selected_code"].get("code"):
        selected_code_str = (
            f"{debug_info['selected_code']['code']} "
            f"({debug_info['selected_code']['description']}) "
            f"conf={debug_info['selected_code']['confidence']:.2f}"
        )

    debug_info["fast_summary"] = (
        f"Specialty: {debug_info['stages'].get('specialty_routing', {}).get('specialty_value', '?')} | "
        f"Selected: {selected_code_str} | "
        f"Confidence: {debug_info['confidence']:.2f} | "
        f"Status: {debug_info['status']} | "
        f"Time: {debug_info['processing_time_ms']}ms"
    )

    return debug_info


@router.get("/pipeline", dependencies=[Depends(require_admin)])
async def debug_pipeline_get(request: Request):
    """Return usage info for the debug pipeline endpoint."""
    return {
        "endpoint": "/debug/pipeline",
        "method": "POST",
        "description": "Trace actual code assignment step by step through the medical coding pipeline.",
        "usage": "POST /debug/pipeline with JSON body: {\"note\": \"clinical note text\", \"note_id\": \"optional-id\"}",
        "example_request": {
            "note": "Patient presents after fall from ladder. Complaint of head injury. Observed in ED for 4 hours.",
            "note_id": "trauma-001",
        },
        "response_fields": {
            "stages.evidence_extraction": "Entities extracted from the note (symptoms, trauma, encounter type)",
            "stages.specialty_routing": "Hard specialty routing result with allowed/blocked ontologies",
            "stages.legacy_evidence_extraction": "Legacy Keyword→ICD term map matches",
            "stages.retrieval": "Hybrid retrieval (BM25 + ontology) top codes",
            "stages.pipeline_execution": "Full AgentOrchestrator pipeline output",
            "stages.candidate_codes": "All candidate codes with confidence scores",
            "stages.v14_pipeline": "Optional V14 trace for additional debug data",
            "selected_code": "Final primary diagnosis code and metadata",
            "confidence": "Overall confidence score",
            "errors": "Any errors encountered per stage",
        },
    }
