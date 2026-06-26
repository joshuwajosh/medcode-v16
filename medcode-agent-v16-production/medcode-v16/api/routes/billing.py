"""
MedCode AI V19 — Billing API Routes
====================================
AAPC Module 5 & 8: Billing automation and performance analytics
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/v19/billing", tags=["billing"])


class GenerateClaimRequest(BaseModel):
    cpt_codes: List[Dict]
    icd_codes: List[Dict]
    patient_info: Optional[Dict] = None
    provider_info: Optional[Dict] = None


class ValidateClaimRequest(BaseModel):
    cpt_codes: List[Dict]
    icd_codes: List[Dict]
    patient_info: Optional[Dict] = None
    provider_info: Optional[Dict] = None


@router.post("/generate-claim")
async def generate_claim(body: GenerateClaimRequest) -> Dict[str, Any]:
    """Generate a medical claim from coded data."""
    from billing.claim_engine import get_claim_generator

    generator = get_claim_generator()
    claim = generator.generate_claim(
        cpt_codes=body.cpt_codes,
        icd_codes=body.icd_codes,
        patient_info=body.patient_info,
        provider_info=body.provider_info,
    )
    return {
        "claim_id": claim.claim_id,
        "total_charges": claim.total_charges,
        "items": [
            {
                "cpt_code": item.cpt_code,
                "description": item.cpt_description,
                "icd_codes": item.icd_codes,
                "modifiers": item.modifiers,
                "charge": item.charge_amount,
            }
            for item in claim.items
        ],
        "place_of_service": claim.place_of_service,
        "status": claim.status,
    }


@router.post("/validate-claim")
async def validate_claim(body: ValidateClaimRequest) -> Dict[str, Any]:
    """Validate a claim before submission."""
    from billing.claim_engine import get_claim_generator, get_claim_validator, get_denial_predictor

    generator = get_claim_generator()
    claim = generator.generate_claim(
        cpt_codes=body.cpt_codes,
        icd_codes=body.icd_codes,
        patient_info=body.patient_info,
        provider_info=body.provider_info,
    )

    validator = get_claim_validator()
    validation = validator.validate(claim)

    predictor = get_denial_predictor()
    denial = predictor.predict_denial(claim, validation)

    return {
        "claim_id": claim.claim_id,
        "validation": {
            "passed": validation.passed,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "checks_performed": validation.checks_performed,
        },
        "denial_prediction": {
            "probability": denial.denial_probability,
            "risk_level": denial.risk_level,
            "risk_factors": denial.risk_factors,
            "recommendations": denial.recommendations,
            "top_denial_reasons": denial.top_denial_reasons,
        },
    }


@router.post("/analyze-batch")
async def analyze_claims_batch(claims: List[Dict]) -> Dict[str, Any]:
    """Analyze a batch of claims for revenue cycle insights."""
    from billing.claim_engine import get_revenue_optimizer

    optimizer = get_revenue_optimizer()
    analysis = optimizer.analyze_claims_batch(claims)
    return analysis


@router.get("/denial-patterns")
async def denial_patterns() -> Dict[str, Any]:
    """Get common denial patterns and prevention strategies."""
    from billing.claim_engine import DENIAL_PATTERNS

    return {
        "patterns": [
            {
                "name": name,
                "category": info["category"],
                "prevention": info["prevention"],
            }
            for name, info in DENIAL_PATTERNS.items()
        ]
    }


@router.get("/pos-codes")
async def place_of_service_codes() -> Dict[str, Any]:
    """Get place of service code descriptions."""
    from billing.claim_engine import POS_DESCRIPTIONS
    return {"pos_codes": POS_DESCRIPTIONS}


# ── Dashboard List Endpoint ────────────────────────────────────────


@router.get("/batches")
async def list_claims_batches(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    payer: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """List claims for the admin dashboard claims tab."""
    from billing.claim_tracker import ClaimTracker

    tracker = ClaimTracker()
    all_claims = tracker.list_claims(limit=5000)

    if status:
        all_claims = [c for c in all_claims if (c.get("status") or "").lower() == status.lower()]
    if payer:
        all_claims = [c for c in all_claims if payer.lower() in (c.get("payer_name") or "").lower()]
    if date_from:
        all_claims = [c for c in all_claims if (c.get("created_at") or "") >= date_from]
    if date_to:
        all_claims = [c for c in all_claims if (c.get("created_at") or "") <= date_to + "T23:59:59"]

    total = len(all_claims)
    start = (max(1, page) - 1) * limit
    claims = all_claims[start: start + limit]

    return {"claims": claims, "total": total, "page": page, "limit": limit}


# ── CMS-1500 / UB-04 / EDI 837 / Submission Workflow Routes ────────


class CMS1500Request(BaseModel):
    cpt_codes: List[Dict]
    icd_codes: List[Dict]
    patient_info: Optional[Dict] = None
    provider_info: Optional[Dict] = None


@router.post("/cms1500")
async def generate_cms1500(body: CMS1500Request) -> Dict[str, Any]:
    """Generate CMS-1500 (professional claim) form data."""
    from billing.claim_engine import get_claim_generator
    from billing.cms1500_generator import CMS1500Generator

    generator = get_claim_generator()
    claim = generator.generate_claim(
        cpt_codes=body.cpt_codes,
        icd_codes=body.icd_codes,
        patient_info=body.patient_info,
        provider_info=body.provider_info,
    )
    cms_gen = CMS1500Generator()
    form_data = cms_gen.generate(claim)
    return form_data


class UB04Request(BaseModel):
    cpt_codes: List[Dict]
    icd_codes: List[Dict]
    patient_info: Optional[Dict] = None
    provider_info: Optional[Dict] = None


@router.post("/ub04")
async def generate_ub04(body: UB04Request) -> Dict[str, Any]:
    """Generate UB-04 (institutional claim) form data."""
    from billing.claim_engine import get_claim_generator
    from billing.ub04_generator import UB04Generator

    generator = get_claim_generator()
    claim = generator.generate_claim(
        cpt_codes=body.cpt_codes,
        icd_codes=body.icd_codes,
        patient_info=body.patient_info,
        provider_info=body.provider_info,
    )
    claim.claim_type = "institutional"
    ub_gen = UB04Generator()
    form_data = ub_gen.generate(claim)
    return form_data


class EDI837Request(BaseModel):
    cpt_codes: List[Dict]
    icd_codes: List[Dict]
    patient_info: Optional[Dict] = None
    provider_info: Optional[Dict] = None
    edi_type: str = "837P"


@router.post("/edi-837")
async def generate_edi_837(body: EDI837Request) -> Dict[str, Any]:
    """Generate EDI 837 (professional or institutional) file."""
    from billing.claim_engine import get_claim_generator
    from billing.edi_837 import EDI837Generator

    generator = get_claim_generator()
    claim = generator.generate_claim(
        cpt_codes=body.cpt_codes,
        icd_codes=body.icd_codes,
        patient_info=body.patient_info,
        provider_info=body.provider_info,
    )

    edi_gen = EDI837Generator()
    if body.edi_type.upper() == "837I":
        result = edi_gen.generate_837i(claim)
    else:
        result = edi_gen.generate_837p(claim)

    return result


class SubmitClaimRequest(BaseModel):
    cpt_codes: List[Dict]
    icd_codes: List[Dict]
    patient_info: Optional[Dict] = None
    provider_info: Optional[Dict] = None


@router.post("/submit-claim")
async def submit_claim(body: SubmitClaimRequest) -> Dict[str, Any]:
    """Execute full claim submission workflow: generate -> validate -> EDI -> track."""
    from billing.submission_workflow import ClaimSubmissionWorkflow

    workflow = ClaimSubmissionWorkflow()
    claim_data = {
        "cpt_codes": body.cpt_codes,
        "icd_codes": body.icd_codes,
        "patient_info": body.patient_info or {},
        "provider_info": body.provider_info or {},
    }
    result = workflow.full_submit(claim_data)
    return result


@router.get("/claim-status/{claim_id}")
async def get_claim_status(claim_id: str) -> Dict[str, Any]:
    """Check claim status and history."""
    from billing.claim_tracker import ClaimTracker

    tracker = ClaimTracker()
    status = tracker.get_status(claim_id)
    history = tracker.get_history(claim_id)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return {
        "status": status,
        "history": history,
    }


@router.get("/payer-rules/{payer}")
async def get_payer_rules(payer: str) -> Dict[str, Any]:
    """Get payer-specific rules and requirements."""
    from billing.payer_rules import PayerRules

    rules = PayerRules()
    config = rules.get_payer_config(payer)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"No configuration found for payer '{payer}'",
        )

    return {
        "payer_name": payer,
        "config": config,
    }
