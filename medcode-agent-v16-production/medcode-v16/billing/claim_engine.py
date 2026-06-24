"""
MedCode AI V19 — Automated Claim Management Engine
====================================================
AAPC Module 5: AI Applications in Medical Billing
- Automated claim generation from coded data
- Claim validation before submission
- Predictive denial analytics
- Revenue cycle optimization
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time


@dataclass
class ClaimItem:
    """Single line item in a medical claim."""
    cpt_code: str = ""
    cpt_description: str = ""
    icd_codes: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    units: int = 1
    charge_amount: float = 0.0
    place_of_service: str = "11"  # 11=Office, 21=Inpatient, 23=ED
    diagnosis_pointers: List[int] = field(default_factory=list)


@dataclass
class Claim:
    """Complete medical claim (CMS-1500 / UB-04 equivalent)."""
    claim_id: str = ""
    patient_name: str = ""
    patient_dob: str = ""
    patient_sex: str = ""
    insurance_id: str = ""
    payer_name: str = ""
    provider_npi: str = ""
    provider_name: str = ""
    facility_npi: str = ""
    date_of_service: str = ""
    date_of_birth: str = ""
    place_of_service: str = "11"
    items: List[ClaimItem] = field(default_factory=list)
    total_charges: float = 0.0
    total_allowed: float = 0.0
    claim_type: str = "professional"  # professional, institutional, pharmacy
    status: str = "draft"
    denial_risk: str = "low"
    denial_probability: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim_id,
            "patient_name": self.patient_name,
            "patient_dob": self.patient_dob,
            "patient_sex": self.patient_sex,
            "insurance_id": self.insurance_id,
            "payer_name": self.payer_name,
            "provider_npi": self.provider_npi,
            "provider_name": self.provider_name,
            "facility_npi": self.facility_npi,
            "date_of_service": self.date_of_service,
            "date_of_birth": self.date_of_birth,
            "place_of_service": self.place_of_service,
            "items": [
                {
                    "cpt_code": item.cpt_code,
                    "cpt_description": item.cpt_description,
                    "icd_codes": item.icd_codes,
                    "modifiers": item.modifiers,
                    "units": item.units,
                    "charge_amount": item.charge_amount,
                    "place_of_service": item.place_of_service,
                    "diagnosis_pointers": item.diagnosis_pointers,
                }
                for item in self.items
            ],
            "total_charges": self.total_charges,
            "total_allowed": self.total_allowed,
            "claim_type": self.claim_type,
            "status": self.status,
            "denial_risk": self.denial_risk,
            "denial_probability": self.denial_probability,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
        }


@dataclass
class DenialPrediction:
    """Predicted denial risk for a claim."""
    claim_id: str = ""
    denial_probability: float = 0.0
    risk_level: str = "low"
    risk_factors: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    top_denial_reasons: List[str] = field(default_factory=list)


@dataclass
class ClaimValidation:
    """Validation result for a claim."""
    claim_id: str = ""
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_performed: List[str] = field(default_factory=list)


# Common denial reasons and their patterns
DENIAL_PATTERNS = {
    "missing_modifier": {
        "keywords": ["modifier", "25", "59", "76", "77"],
        "prevention": "Add appropriate modifier to separate services",
        "category": "documentation",
    },
    "bundling_violation": {
        "keywords": ["bundled", "inclusive", "component"],
        "prevention": "Check NCCI edits for code pair conflicts",
        "category": "coding",
    },
    "medical_necessity": {
        "keywords": ["medical necessity", "not supported", "not documented"],
        "prevention": "Ensure diagnosis supports procedure medical necessity",
        "category": "documentation",
    },
    "authorization_required": {
        "keywords": ["prior auth", "preauthorization", "authorization"],
        "prevention": "Obtain prior authorization before procedure",
        "category": "administrative",
    },
    "timely_filing": {
        "keywords": ["timely filing", "submission deadline"],
        "prevention": "Submit claim within payer filing deadline",
        "category": "administrative",
    },
    "coordination_of_benefits": {
        "keywords": ["cob", "coordination", "primary", "secondary"],
        "prevention": "Verify patient insurance coverage and COB",
        "category": "administrative",
    },
    "incorrect_patient_info": {
        "keywords": ["patient info", "demographic", "eligibility"],
        "prevention": "Verify patient demographics and insurance eligibility",
        "category": "administrative",
    },
    "duplicate_claim": {
        "keywords": ["duplicate", "already submitted", "previously billed"],
        "prevention": "Check for existing claims before submission",
        "category": "administrative",
    },
    "non_covered_service": {
        "keywords": ["not covered", "exclusion", "non-covered"],
        "prevention": "Verify payer coverage for specific service",
        "category": "coverage",
    },
    "exceeds_frequency_limit": {
        "keywords": ["frequency", "limit exceeded", "MUE"],
        "prevention": "Check MUE limits and frequency restrictions",
        "category": "coding",
    },
}

# Place of service descriptions
POS_DESCRIPTIONS = {
    "11": "Office",
    "12": "Home",
    "21": "Inpatient Hospital",
    "22": "Outpatient Hospital",
    "23": "Emergency Department",
    "31": "Skilled Nursing Facility",
    "32": "Nursing Facility",
    "41": "Ambulance - Land",
    "49": "Independent Clinic",
    "51": "Inpatient Psychiatric",
    "53": "Community Mental Health Center",
    "54": "Intermediate Care Facility",
    "56": "Psychiatric Residential Treatment",
    "65": "End-Stage Renal Disease Treatment",
    "71": "Public Health Clinic",
    "72": "Rural Health Clinic",
    "81": "Independent Laboratory",
    "99": "Other",
}


class ClaimGenerator:
    """
    Generates medical claims from coded data.
    Implements AAPC Module 5 concepts.
    """

    def generate_claim(
        self,
        cpt_codes: List[Dict],
        icd_codes: List[Dict],
        patient_info: Optional[Dict] = None,
        provider_info: Optional[Dict] = None,
    ) -> Claim:
        """Generate a claim from coded data."""
        patient = patient_info or {}
        provider = provider_info or {}

        items = []
        for i, cpt in enumerate(cpt_codes):
            item = ClaimItem(
                cpt_code=cpt.get("code", ""),
                cpt_description=cpt.get("description", ""),
                icd_codes=[icd.get("code", "") for icd in icd_codes[:3]],
                modifiers=[cpt.get("modifier", "")] if cpt.get("modifier") else [],
                charge_amount=self._estimate_charge(cpt.get("code", "")),
                place_of_service=patient.get("place_of_service", "11"),
                diagnosis_pointers=list(range(1, min(len(icd_codes) + 1, 4))),
            )
            items.append(item)

        total_charges = sum(item.charge_amount * item.units for item in items)

        claim = Claim(
            claim_id=f"CLM-{int(time.time())}",
            patient_name=patient.get("name", "PATIENT, REDACTED"),
            patient_dob=patient.get("dob", ""),
            patient_sex=patient.get("sex", ""),
            insurance_id=patient.get("insurance_id", ""),
            payer_name=patient.get("payer", ""),
            provider_npi=provider.get("npi", ""),
            provider_name=provider.get("name", ""),
            date_of_service=patient.get("dos", ""),
            place_of_service=patient.get("place_of_service", "11"),
            items=items,
            total_charges=total_charges,
        )

        return claim

    def _estimate_charge(self, cpt_code: str) -> float:
        """Estimate charge amount for a CPT code (simplified)."""
        charge_ranges = {
            "99202": 100, "99203": 175, "99204": 250, "99205": 350,
            "99212": 60, "99213": 120, "99214": 180, "99215": 250,
            "99221": 200, "99222": 280, "99223": 380,
            "99231": 100, "99232": 150, "99233": 220,
            "99238": 150, "99239": 250,
            "99281": 100, "99282": 200, "99283": 300,
            "99284": 400, "99285": 500,
            "99291": 500, "99292": 250,
            "33533": 15000, "33534": 18000, "33535": 22000,
            "47562": 5000, "44970": 4500,
            "27447": 25000, "27130": 22000,
            "29828": 3500, "29827": 4000,
            "63047": 5000, "63048": 2500,
        }
        return charge_ranges.get(cpt_code, 200)


class ClaimValidator:
    """
    Validates claims before submission.
    Implements claim validation checks per AAPC guidelines.
    """

    def validate(self, claim: Claim) -> ClaimValidation:
        """Run all validation checks on a claim."""
        result = ClaimValidation(claim_id=claim.claim_id)
        checks = []

        # Check 1: Required fields
        errors = self._check_required_fields(claim)
        result.errors.extend(errors)
        checks.append("required_fields")

        # Check 2: Diagnosis-procedure linkage
        dx_proc_errors = self._check_dx_procedure_linkage(claim)
        result.errors.extend(dx_proc_errors)
        checks.append("dx_procedure_linkage")

        # Check 3: Modifier requirements
        modifier_warnings = self._check_modifier_requirements(claim)
        result.warnings.extend(modifier_warnings)
        checks.append("modifier_requirements")

        # Check 4: Place of service consistency
        pos_warnings = self._check_pos_consistency(claim)
        result.warnings.extend(pos_warnings)
        checks.append("pos_consistency")

        # Check 5: Duplicate line items
        duplicate_errors = self._check_duplicates(claim)
        result.errors.extend(duplicate_errors)
        checks.append("duplicate_check")

        # Check 6: Valid CPT codes
        cpt_errors = self._check_valid_cpt(claim)
        result.errors.extend(cpt_errors)
        checks.append("cpt_validation")

        result.checks_performed = checks
        result.passed = len(result.errors) == 0
        return result

    def _check_required_fields(self, claim: Claim) -> List[str]:
        errors = []
        if not claim.patient_name:
            errors.append("Missing patient name")
        if not claim.date_of_service:
            errors.append("Missing date of service")
        if not claim.provider_npi:
            errors.append("Missing provider NPI")
        if not claim.payer_name:
            errors.append("Missing payer name")
        if not claim.items:
            errors.append("No line items on claim")
        return errors

    def _check_dx_procedure_linkage(self, claim: Claim) -> List[str]:
        errors = []
        for item in claim.items:
            if not item.icd_codes:
                errors.append(f"CPT {item.cpt_code}: No diagnosis codes linked")
            if item.diagnosis_pointers:
                max_pointer = max(item.diagnosis_pointers)
                if max_pointer > len(item.icd_codes):
                    errors.append(
                        f"CPT {item.cpt_code}: Diagnosis pointer {max_pointer} "
                        f"exceeds available diagnosis codes ({len(item.icd_codes)})"
                    )
        return errors

    def _check_modifier_requirements(self, claim: Claim) -> List[str]:
        warnings = []
        for item in claim.items:
            if item.cpt_code in ["99214", "99215"] and not item.modifiers:
                warnings.append(
                    f"CPT {item.cpt_code}: Consider modifier 25 if separate E/M service"
                )
        return warnings

    def _check_pos_consistency(self, claim: Claim) -> List[str]:
        warnings = []
        for item in claim.items:
            if item.place_of_service == "11" and item.cpt_code.startswith("9922"):
                warnings.append(
                    f"CPT {item.cpt_code}: Hospital code with office POS"
                )
        return warnings

    def _check_duplicates(self, claim: Claim) -> List[str]:
        errors = []
        seen = {}
        for item in claim.items:
            key = (item.cpt_code, tuple(item.modifiers))
            if key in seen:
                errors.append(
                    f"Duplicate line item: CPT {item.cpt_code} with modifiers {item.modifiers}"
                )
            seen[key] = True
        return errors

    def _check_valid_cpt(self, claim: Claim) -> List[str]:
        errors = []
        valid_prefixes = ["99", "10", "11", "19", "20", "27", "29", "33", "34",
                         "35", "36", "37", "38", "39", "42", "43", "44", "45",
                         "47", "48", "49", "50", "51", "52", "53", "54", "55",
                         "58", "59", "60", "61", "62", "63", "64", "65", "66",
                         "67", "68", "69", "70", "71", "72", "73", "74", "75",
                         "76", "77", "78", "88", "90", "92", "93", "94", "95",
                         "96", "97", "99"]
        for item in claim.items:
            code = item.cpt_code
            if len(code) != 5 or not code.isdigit():
                errors.append(f"Invalid CPT code format: {code}")
            elif code[:2] not in valid_prefixes:
                errors.append(f"Unrecognized CPT code prefix: {code}")
        return errors


class DenialPredictor:
    """
    Predicts claim denial risk using pattern analysis.
    Implements AAPC Module 5 predictive analytics concepts.
    """

    def predict_denial(self, claim: Claim, validation: ClaimValidation) -> DenialPrediction:
        """Predict denial probability for a claim."""
        risk_factors = []
        recommendations = []
        risk_score = 0.0

        # Factor 1: Validation errors
        if validation.errors:
            risk_score += min(len(validation.errors) * 0.15, 0.45)
            risk_factors.append({
                "factor": "validation_errors",
                "count": len(validation.errors),
                "impact": "high",
            })
            recommendations.append("Fix all validation errors before submission")

        # Factor 2: Validation warnings
        if validation.warnings:
            risk_score += min(len(validation.warnings) * 0.05, 0.15)
            risk_factors.append({
                "factor": "validation_warnings",
                "count": len(validation.warnings),
                "impact": "medium",
            })

        # Factor 3: Missing modifiers
        missing_mods = sum(1 for item in claim.items if not item.modifiers)
        if missing_mods > 0:
            risk_score += min(missing_mods * 0.05, 0.10)
            risk_factors.append({
                "factor": "missing_modifiers",
                "count": missing_mods,
                "impact": "medium",
            })
            recommendations.append("Add appropriate modifiers (25, 59, 76, etc.)")

        # Factor 4: High-value claims
        if claim.total_charges > 10000:
            risk_score += 0.05
            risk_factors.append({
                "factor": "high_value_claim",
                "amount": claim.total_charges,
                "impact": "low",
            })
            recommendations.append("High-value claim — ensure thorough documentation")

        # Factor 5: Multiple procedures
        if len(claim.items) > 5:
            risk_score += 0.05
            risk_factors.append({
                "factor": "multiple_procedures",
                "count": len(claim.items),
                "impact": "low",
            })
            recommendations.append("Multiple procedures — verify no bundling issues")

        # Factor 6: Emergency department claims
        ed_count = sum(1 for item in claim.items if item.cpt_code.startswith("9928"))
        if ed_count > 0:
            risk_score += 0.03
            risk_factors.append({
                "factor": "ed_claims",
                "count": ed_count,
                "impact": "low",
            })

        # Cap risk score
        risk_score = min(risk_score, 0.99)

        # Determine risk level
        if risk_score >= 0.70:
            risk_level = "high"
        elif risk_score >= 0.40:
            risk_level = "moderate"
        elif risk_score >= 0.20:
            risk_level = "low"
        else:
            risk_level = "minimal"

        # Top denial reasons
        top_reasons = []
        if validation.errors:
            top_reasons.append("Validation errors detected")
        if missing_mods > 0:
            top_reasons.append("Missing required modifiers")
        if claim.total_charges > 10000:
            top_reasons.append("High-value claim scrutiny")

        return DenialPrediction(
            claim_id=claim.claim_id,
            denial_probability=round(risk_score, 3),
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations,
            top_denial_reasons=top_reasons,
        )


class RevenueCycleOptimizer:
    """
    Revenue cycle management analytics.
    Identifies trends and optimization opportunities.
    """

    def analyze_claims_batch(self, claims: List[Dict]) -> Dict:
        """Analyze a batch of claims for revenue cycle insights."""
        total_claims = len(claims)
        if total_claims == 0:
            return {"error": "No claims to analyze"}

        total_charges = sum(c.get("total_charges", 0) for c in claims)
        denial_count = sum(1 for c in claims if c.get("denial_risk") == "high")
        avg_charge = total_charges / total_claims if total_claims > 0 else 0

        # Coding distribution
        cpt_distribution = {}
        for claim in claims:
            for item in claim.get("items", []):
                code = item.get("cpt_code", "")
                if code:
                    cpt_distribution[code] = cpt_distribution.get(code, 0) + 1

        # Top CPT codes
        top_cpt = sorted(cpt_distribution.items(), key=lambda x: x[1], reverse=True)[:10]

        # Denial risk distribution
        risk_distribution = {"minimal": 0, "low": 0, "moderate": 0, "high": 0}
        for claim in claims:
            risk = claim.get("denial_risk", "low")
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1

        return {
            "total_claims": total_claims,
            "total_charges": round(total_charges, 2),
            "average_charge": round(avg_charge, 2),
            "denial_risk_distribution": risk_distribution,
            "high_risk_claims": denial_count,
            "top_cpt_codes": top_cpt,
            "revenue_at_risk": round(
                sum(c.get("total_charges", 0) for c in claims if c.get("denial_risk") == "high"),
                2,
            ),
        }


# Singleton instances
_claim_generator = ClaimGenerator()
_claim_validator = ClaimValidator()
_denial_predictor = DenialPredictor()
_revenue_optimizer = RevenueCycleOptimizer()


def get_claim_generator() -> ClaimGenerator:
    return _claim_generator

def get_claim_validator() -> ClaimValidator:
    return _claim_validator

def get_denial_predictor() -> DenialPredictor:
    return _denial_predictor

def get_revenue_optimizer() -> RevenueCycleOptimizer:
    return _revenue_optimizer
