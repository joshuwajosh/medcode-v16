"""
MedCode AI V19 — Billing API Routes
=====================================
AAPC Module 5 & 8: Billing automation and performance analytics
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional

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
async def generate_claim(body: GenerateClaimRequest):
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
async def validate_claim(body: ValidateClaimRequest):
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
async def analyze_claims_batch(claims: List[Dict]):
    """Analyze a batch of claims for revenue cycle insights."""
    from billing.claim_engine import get_revenue_optimizer
    
    optimizer = get_revenue_optimizer()
    analysis = optimizer.analyze_claims_batch(claims)
    return analysis


@router.get("/denial-patterns")
async def denial_patterns():
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
async def place_of_service_codes():
    """Get place of service code descriptions."""
    from billing.claim_engine import POS_DESCRIPTIONS
    return {"pos_codes": POS_DESCRIPTIONS}
