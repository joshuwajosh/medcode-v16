"""
MedCode AI Agent -- Search Routes
===================================
GET /api/search -- Semantic search
GET /api/validate/{code} -- Code validation
GET /api/hierarchy/{code} -- Hierarchy exploration
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from core.models import CodeCandidate
from search.code_validator import CodeValidator
from knowledge.code_systems import validate_code_format, get_code_system
from knowledge.coding_guidelines import needs_seventh_char, requires_laterality, is_billable

router = APIRouter(prefix="/api", tags=["search"])
v1_router = APIRouter(prefix="/api/v1", tags=["search"])


def get_omop(request: Request):
    return request.app.state.omop


def get_searcher(request: Request):
    return request.app.state.searcher


@router.get("/search")
@v1_router.get("/search")
async def search_codes(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query"),
    vocab: str = Query("ICD10CM", description="Vocabulary ID"),
    limit: int = Query(15, ge=1, le=50),
):
    """Semantic search for medical codes."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    searcher = get_searcher(request)
    
    try:
        if searcher is not None:
            results = searcher.search_direct(
                query=q.strip(),
                vocabulary_ids=[vocab],
                limit=limit,
            )
            return {
                "query": q,
                "vocabulary": vocab,
                "results": [r.to_dict() for r in results],
                "count": len(results),
            }
        else:
            # Fallback: search local ICD-10 database directly
            from search.icd10_database import search_with_vocabulary
            items = search_with_vocabulary(q.strip(), [vocab], limit)
            return {
                "query": q,
                "vocabulary": vocab,
                "results": [
                    {
                        "code": item.get("concept_code", ""),
                        "name": item.get("concept_name", ""),
                        "vocabulary": item.get("vocabulary_id", vocab),
                        "similarity_score": item.get("similarity_score", 0.0),
                    }
                    for item in items
                ],
                "count": len(items),
                "source": "local_db",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/{code}")
@v1_router.get("/validate/{code}")
async def validate_code(
    request: Request,
    code: str,
    vocab: str = Query("ICD10CM"),
):
    """Validate a medical code and get its metadata."""
    if not code.strip():
        raise HTTPException(status_code=400, detail="Code is required")

    # Format validation
    valid_format = validate_code_format(code, vocab)
    
    # OMOP validation
    omop = get_omop(request)
    concept = None
    if omop:
        try:
            concept = omop.validate_code(vocab, code.upper())
        except Exception:
            pass

    # Guideline checks
    needs_seventh = needs_seventh_char(code)
    has_laterality = requires_laterality(code)
    billable = is_billable(code)

    # Get code system info
    system_info = get_code_system(vocab)

    return {
        "code": code.upper(),
        "vocabulary": vocab,
        "valid_format": valid_format,
        "exists_in_omop": concept is not None,
        "concept_name": concept.concept_name if concept else "",
        "is_billable": billable,
        "requires_7th_char": needs_seventh,
        "requires_laterality": has_laterality,
        "code_system_name": system_info.name if system_info else vocab,
    }


@router.get("/hierarchy/{code}")
@v1_router.get("/hierarchy/{code}")
async def get_hierarchy(
    request: Request,
    code: str,
    vocab: str = Query("ICD10CM"),
    direction: str = Query("both", pattern="^(parents|children|both)$"),
    depth: int = Query(1, ge=1, le=3),
):
    """Get hierarchy (parents/children) for a medical code."""
    omop = get_omop(request)
    if not omop:
        raise HTTPException(status_code=503, detail="OMOP client not available")

    result = {"code": code.upper(), "vocabulary": vocab, "parents": [], "children": []}

    try:
        if direction in ("parents", "both"):
            parents = omop.get_parents(vocab, code.upper())
            result["parents"] = [
                {"code": p.concept_code, "name": p.concept_name, "vocabulary": p.vocabulary_id}
                for p in parents[:10]
            ]

        if direction in ("children", "both"):
            children = omop.get_children(vocab, code.upper())
            result["children"] = [
                {"code": c.concept_code, "name": c.concept_name, "vocabulary": c.vocabulary_id}
                for c in children[:15]
            ]

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/map/{code}")
@v1_router.get("/map/{code}")
async def map_code(
    request: Request,
    code: str,
    source: str = Query("ICD10CM", description="Source vocabulary"),
    target: str = Query("SNOMED", description="Target vocabulary"),
):
    """Cross-vocabulary mapping (ICD-10 ↔ SNOMED / RxNorm / etc.)."""
    omop = get_omop(request)
    if not omop:
        raise HTTPException(status_code=503, detail="OMOP client not available")
    try:
        results = omop.map_code(code.upper(), source, target)
        return {
            "source_code": code.upper(),
            "source_vocabulary": source,
            "target_vocabulary": target,
            "mappings": [
                {"code": r.concept_code, "name": r.concept_name, "vocabulary": r.vocabulary_id}
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest")
@v1_router.get("/suggest")
async def suggest_codes(
    request: Request,
    q: str = Query(..., min_length=1, description="Prefix for autocomplete"),
    limit: int = Query(8, ge=1, le=25),
):
    """Autocomplete suggestions as the user types."""
    omop = get_omop(request)
    if not omop:
        raise HTTPException(status_code=503, detail="OMOP client not available")
    try:
        results = omop.suggest(q, limit=limit)
        return {"query": q, "suggestions": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
