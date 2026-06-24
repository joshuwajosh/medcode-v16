"""
MedCode AI — Claim Submission Workflow
========================================
Orchestrates the complete claim submission process:
generate -> validate -> check payer rules -> generate EDI -> track status.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
import time


class ClaimSubmissionWorkflow:
    """
    Complete claim submission workflow orchestrator.
    Coordinates all billing subsystems into a single submission flow.
    """

    def full_submit(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete claim submission workflow.

        Args:
            claim_data: Dict with claim fields (patient_info, provider_info,
                       cpt_codes, icd_codes, or a pre-built Claim dict).

        Returns:
            Dict with claim_id, validation_result, payer_requirements,
            edi_file_path, tracking_id, and full workflow status.
        """
        result: Dict[str, Any] = {
            "workflow_steps": [],
            "success": False,
        }

        # Step 1: Generate or accept claim
        step1 = self._step_generate_claim(claim_data)
        result["workflow_steps"].append(step1)
        if not step1.get("success"):
            result["error"] = step1.get("error", "Claim generation failed")
            return result

        claim = step1["claim"]

        # Step 2: Validate claim
        step2 = self._step_validate(claim)
        result["workflow_steps"].append(step2)
        result["validation_result"] = step2.get("validation")
        if not step2.get("success"):
            result["error"] = "Validation failed"
            return result

        # Step 3: Check payer rules
        step3 = self._step_check_payer_rules(claim)
        result["workflow_steps"].append(step3)
        result["payer_requirements"] = step3.get("payer_requirements")

        # Step 4: Generate EDI file
        step4 = self._step_generate_edi(claim)
        result["workflow_steps"].append(step4)
        result["edi_file_path"] = step4.get("edi_file_path")

        # Step 5: Track status
        step5 = self._step_track_status(claim)
        result["workflow_steps"].append(step5)
        result["claim_id"] = step5.get("claim_id")
        result["tracking_id"] = step5.get("tracking_id")

        # Step 6: Generate form data (CMS-1500 or UB-04)
        step6 = self._step_generate_form(claim)
        result["workflow_steps"].append(step6)
        result["form_data"] = step6.get("form_data")
        result["form_type"] = step6.get("form_type")

        result["success"] = True
        result["total_charges"] = self._get_total_charges(claim)
        result["payer_name"] = self._get_payer_name(claim)

        return result

    def _step_generate_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Generate claim from coded data."""
        from billing.claim_engine import get_claim_generator

        step = {"name": "generate_claim", "success": False}

        try:
            generator = get_claim_generator()

            if "items" in claim_data and "claim_id" in claim_data:
                claim = self._dict_to_claim(claim_data)
                step["claim"] = claim
                step["success"] = True
                step["claim_id"] = claim_data.get("claim_id", "")
            else:
                cpt_codes = claim_data.get("cpt_codes", [])
                icd_codes = claim_data.get("icd_codes", [])
                patient_info = claim_data.get("patient_info", {})
                provider_info = claim_data.get("provider_info", {})

                claim = generator.generate_claim(
                    cpt_codes=cpt_codes,
                    icd_codes=icd_codes,
                    patient_info=patient_info,
                    provider_info=provider_info,
                )
                step["claim"] = claim
                step["success"] = True
                step["claim_id"] = claim.claim_id

        except Exception as e:
            step["error"] = str(e)

        return step

    def _step_validate(self, claim) -> Dict[str, Any]:
        """Step 2: Validate claim."""
        from billing.claim_engine import get_claim_validator, get_denial_predictor

        step = {"name": "validate", "success": False}

        try:
            validator = get_claim_validator()
            validation = validator.validate(claim)

            predictor = get_denial_predictor()
            denial = predictor.predict_denial(claim, validation)

            step["validation"] = {
                "passed": validation.passed,
                "errors": validation.errors,
                "warnings": validation.warnings,
                "checks_performed": validation.checks_performed,
            }
            step["denial_prediction"] = {
                "probability": denial.denial_probability,
                "risk_level": denial.risk_level,
                "risk_factors": denial.risk_factors,
                "recommendations": denial.recommendations,
                "top_denial_reasons": denial.top_denial_reasons,
            }
            step["success"] = True

        except Exception as e:
            step["error"] = str(e)

        return step

    def _step_check_payer_rules(self, claim) -> Dict[str, Any]:
        """Step 3: Check payer-specific rules."""
        from billing.payer_rules import PayerRules

        step = {"name": "check_payer_rules", "success": False}

        try:
            payer_rules = PayerRules()
            payer_name = self._get_payer_name(claim)

            requirements = payer_rules.check_payer_requirements(claim, payer_name)
            step["payer_requirements"] = requirements
            step["success"] = True

        except Exception as e:
            step["error"] = str(e)

        return step

    def _step_generate_edi(self, claim) -> Dict[str, Any]:
        """Step 4: Generate EDI 837 file."""
        from billing.edi_837 import EDI837Generator

        step = {"name": "generate_edi", "success": False}

        try:
            edi_gen = EDI837Generator()
            claim_type = self._get_claim_type(claim)

            if claim_type == "institutional":
                edi_result = edi_gen.generate_837i(claim)
            else:
                edi_result = edi_gen.generate_837p(claim)

            claim_id = self._get_claim_id(claim)
            edi_file_path = f"data/{claim_id}_837{'i' if claim_type == 'institutional' else 'p'}.edi"

            step["edi_type"] = edi_result.get("edi_type", "")
            step["segment_count"] = edi_result.get("segment_count", 0)
            step["edi_file_path"] = edi_file_path
            step["edi_content"] = edi_result.get("edi_content", "")
            step["isa_control_number"] = edi_result.get("isa_control_number", 0)
            step["success"] = True

        except Exception as e:
            step["error"] = str(e)

        return step

    def _step_track_status(self, claim) -> Dict[str, Any]:
        """Step 5: Register claim in tracking system."""
        from billing.claim_tracker import ClaimTracker

        step = {"name": "track_status", "success": False}

        try:
            tracker = ClaimTracker()
            claim_id = self._get_claim_id(claim)

            tracker.submit(
                claim_id=claim_id,
                patient_name=self._get_patient_name(claim),
                payer_name=self._get_payer_name(claim),
                provider_npi=self._get_provider_npi(claim),
                total_charges=self._get_total_charges(claim),
                claim_type=self._get_claim_type(claim),
            )

            status_result = tracker.update_status(claim_id, "validated", "Auto-validated by workflow")

            step["claim_id"] = claim_id
            step["tracking_id"] = claim_id
            step["status"] = status_result.get("new_status", "validated")
            step["success"] = True

        except Exception as e:
            step["error"] = str(e)

        return step

    def _step_generate_form(self, claim) -> Dict[str, Any]:
        """Step 6: Generate CMS-1500 or UB-04 form data."""
        step = {"name": "generate_form", "success": False}

        try:
            claim_type = self._get_claim_type(claim)

            if claim_type == "institutional":
                from billing.ub04_generator import UB04Generator
                gen = UB04Generator()
                form_data = gen.generate(claim)
                step["form_type"] = "UB-04"
            else:
                from billing.cms1500_generator import CMS1500Generator
                gen = CMS1500Generator()
                form_data = gen.generate(claim)
                step["form_type"] = "CMS-1500"

            step["form_data"] = form_data
            step["success"] = True

        except Exception as e:
            step["error"] = str(e)

        return step

    def _dict_to_claim(self, data: Dict[str, Any]):
        """Convert a dict to a Claim object."""
        from billing.claim_engine import Claim, ClaimItem

        items_data = data.get("items", [])
        items = []
        for item_data in items_data:
            if isinstance(item_data, dict):
                items.append(ClaimItem(
                    cpt_code=item_data.get("cpt_code", ""),
                    cpt_description=item_data.get("cpt_description", ""),
                    icd_codes=item_data.get("icd_codes", []),
                    modifiers=item_data.get("modifiers", []),
                    units=item_data.get("units", 1),
                    charge_amount=item_data.get("charge_amount", 0.0),
                    place_of_service=item_data.get("place_of_service", "11"),
                    diagnosis_pointers=item_data.get("diagnosis_pointers", []),
                ))

        return Claim(
            claim_id=data.get("claim_id", f"CLM-{int(time.time())}"),
            patient_name=data.get("patient_name", ""),
            patient_dob=data.get("patient_dob", ""),
            patient_sex=data.get("patient_sex", ""),
            insurance_id=data.get("insurance_id", ""),
            payer_name=data.get("payer_name", ""),
            provider_npi=data.get("provider_npi", ""),
            provider_name=data.get("provider_name", ""),
            facility_npi=data.get("facility_npi", ""),
            date_of_service=data.get("date_of_service", ""),
            date_of_birth=data.get("date_of_birth", ""),
            place_of_service=data.get("place_of_service", "11"),
            items=items,
            total_charges=data.get("total_charges", 0.0),
            total_allowed=data.get("total_allowed", 0.0),
            claim_type=data.get("claim_type", "professional"),
        )

    def _get_claim_id(self, claim) -> str:
        if isinstance(claim, dict):
            return claim.get("claim_id", "")
        if hasattr(claim, "to_dict"):
            return claim.to_dict().get("claim_id", "")
        return getattr(claim, "claim_id", "")

    def _get_patient_name(self, claim) -> str:
        if isinstance(claim, dict):
            return claim.get("patient_name", "")
        if hasattr(claim, "to_dict"):
            return claim.to_dict().get("patient_name", "")
        return getattr(claim, "patient_name", "")

    def _get_payer_name(self, claim) -> str:
        if isinstance(claim, dict):
            return claim.get("payer_name", "")
        if hasattr(claim, "to_dict"):
            return claim.to_dict().get("payer_name", "")
        return getattr(claim, "payer_name", "")

    def _get_provider_npi(self, claim) -> str:
        if isinstance(claim, dict):
            return claim.get("provider_npi", "")
        if hasattr(claim, "to_dict"):
            return claim.to_dict().get("provider_npi", "")
        return getattr(claim, "provider_npi", "")

    def _get_total_charges(self, claim) -> float:
        if isinstance(claim, dict):
            return claim.get("total_charges", 0.0)
        if hasattr(claim, "to_dict"):
            return claim.to_dict().get("total_charges", 0.0)
        return getattr(claim, "total_charges", 0.0)

    def _get_claim_type(self, claim) -> str:
        if isinstance(claim, dict):
            return claim.get("claim_type", "professional")
        if hasattr(claim, "to_dict"):
            return claim.to_dict().get("claim_type", "professional")
        return getattr(claim, "claim_type", "professional")
