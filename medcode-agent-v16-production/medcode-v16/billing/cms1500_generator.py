"""
MedCode AI — CMS-1500 (Professional Claim) Form Generation
============================================================
Generates structured JSON data mapping all 33 CMS-1500 boxes
for PDF rendering and EDI transmission.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# CMS-1500 box descriptions (all 33 boxes)
CMS1500_BOXES = {
    "1": "Type of Insurance",
    "2": "Patient's Name",
    "3": "Patient's Birth Date",
    "4": "Patient's Sex",
    "5": "Patient's Address",
    "6": "Patient Relationship to Insured",
    "7": "Insured's Name",
    "8": "Insured's Birth Date",
    "9": "Insured's Sex",
    "9a": "Insured's ID Number",
    "9c": "Group Number",
    "10": "Is Condition Related to Employment",
    "11": "Is Condition Related to Auto Accident",
    "12": "Is Condition Related to Other Accident",
    "13": "Reserved for Pub 9000",
    "14": "Date of Illness/Injury",
    "14a": "Date Patient Unable to Work",
    "14b": "Date Patient Returned to Work",
    "15": "Date of First Consultation",
    "16": "Date Patient Last Seen",
    "17": "Name/Qual of Referring Provider",
    "17a": "Referring Provider NPI",
    "18": "Hospitalization Dates",
    "19": "Reserved for Pub 9000",
    "20": "Outside Lab Charges",
    "21": "Diagnosis or Nature of Illness/Injury (ICD codes)",
    "22": "Resubmission Code",
    "23": "Prior Authorization Number",
    "24a": "Date(s) of Service",
    "24b": "Place of Service",
    "24c": "EMG",
    "24d": "CPT/HCPCS Code",
    "24e": "Modifiers",
    "24f": "Diagnosis Pointers",
    "24g": "Charges",
    "24h": "Days or Units",
    "24i": "EPSDT",
    "24j": "Rendering Provider NPI",
    "25": "Federal Tax ID Number",
    "26": "Patient's Account Number",
    "27": "Assignment of Benefits Indicator",
    "28": "Total Charge",
    "29": "Amount Paid",
    "30": "Balance Due",
    "31": "Signature of Physician/Supplier",
    "32": "Facility Name and Address",
    "32a": "Facility NPI",
    "33": "Billing Provider Info and Phone",
    "33a": "Billing Provider NPI",
}


class CMS1500Generator:
    """
    Generates CMS-1500 (professional claim) form data
    in structured JSON format for PDF rendering.
    """

    def generate(self, claim) -> Dict[str, Any]:
        """
        Generate CMS-1500 form data from a Claim object or dict.

        Args:
            claim: Claim dataclass or dict with claim fields.

        Returns:
            Dict mapping all CMS-1500 boxes to values.
        """
        c = self._to_dict(claim)

        diagnosis_codes = self._extract_diagnosis_codes(c)
        line_items = c.get("items", [])
        provider_npi = c.get("provider_npi", "")
        facility_npi = c.get("facility_npi", "")

        form: Dict[str, Any] = {
            "form_type": "CMS-1500",
            "version": "02/12",
            "claim_id": c.get("claim_id", ""),
            "boxes": {},
        }

        boxes = form["boxes"]

        # Box 1: Type of Health Insurance
        boxes["1"] = self._map_insurance_type(c.get("payer_name", ""))

        # Box 2: Patient's Name
        boxes["2"] = c.get("patient_name", "")

        # Box 3: Patient's Birth Date
        boxes["3"] = c.get("patient_dob", c.get("date_of_birth", ""))

        # Box 4: Patient's Sex
        boxes["4"] = c.get("patient_sex", "")

        # Box 5: Patient's Address (not in claim data)
        boxes["5"] = ""

        # Box 6: Patient Relationship to Insured
        boxes["6"] = "Self"

        # Box 7: Insured's Name (if different from patient)
        boxes["7"] = c.get("patient_name", "")

        # Box 8: Insured's Birth Date
        boxes["8"] = c.get("patient_dob", c.get("date_of_birth", ""))

        # Box 9: Insured's Sex
        boxes["9"] = c.get("patient_sex", "")

        # Box 9a: Insured's ID Number
        boxes["9a"] = c.get("insurance_id", "")

        # Box 9c: Group Number
        boxes["9c"] = ""

        # Box 10-12: Condition related flags
        boxes["10"] = "No"
        boxes["11"] = "No"
        boxes["12"] = "No"

        # Box 13: Reserved
        boxes["13"] = ""

        # Box 14: Date of Illness/Injury (use date of service)
        boxes["14"] = c.get("date_of_service", "")
        boxes["14a"] = ""
        boxes["14b"] = ""

        # Box 15: Date of First Consultation
        boxes["15"] = ""

        # Box 16: Date Patient Last Seen
        boxes["16"] = c.get("date_of_service", "")

        # Box 17: Referring Provider Name
        boxes["17"] = c.get("provider_name", "")
        boxes["17a"] = provider_npi

        # Box 18: Hospitalization Dates
        boxes["18"] = ""

        # Box 19: Reserved
        boxes["19"] = ""

        # Box 20: Outside Lab Charges
        boxes["20"] = 0.0

        # Box 21: Diagnosis Codes
        boxes["21"] = self._format_diagnosis_pointers(diagnosis_codes)

        # Box 22: Resubmission Code
        boxes["22"] = ""

        # Box 23: Prior Authorization Number
        boxes["23"] = ""

        # Box 24: Line items
        boxes["24"] = self._format_line_items(
            line_items, diagnosis_codes
        )

        # Box 25: Federal Tax ID
        boxes["25"] = ""

        # Box 26: Patient's Account Number
        boxes["26"] = c.get("claim_id", "")

        # Box 27: Assignment of Benefits
        boxes["27"] = "Yes"

        # Box 28: Total Charge
        boxes["28"] = c.get("total_charges", 0.0)

        # Box 29: Amount Paid
        boxes["29"] = 0.0

        # Box 30: Balance Due
        boxes["30"] = c.get("total_charges", 0.0)

        # Box 31: Signature
        boxes["31"] = "Signature on File"

        # Box 32: Facility Name and Address
        boxes["32"] = c.get("facility_name", "")
        boxes["32a"] = facility_npi

        # Box 33: Billing Provider
        boxes["33"] = c.get("provider_name", "")
        boxes["33a"] = provider_npi

        # Add summary
        form["summary"] = {
            "total_line_items": len(line_items),
            "total_diagnosis_codes": len(diagnosis_codes),
            "total_charges": c.get("total_charges", 0.0),
            "place_of_service": c.get("place_of_service", "11"),
            "claim_type": "professional",
        }

        return form

    def _to_dict(self, claim) -> Dict[str, Any]:
        """Convert Claim dataclass or dict to dict."""
        if isinstance(claim, dict):
            return claim
        return {
            "claim_id": getattr(claim, "claim_id", ""),
            "patient_name": getattr(claim, "patient_name", ""),
            "patient_dob": getattr(claim, "patient_dob", ""),
            "patient_sex": getattr(claim, "patient_sex", ""),
            "insurance_id": getattr(claim, "insurance_id", ""),
            "payer_name": getattr(claim, "payer_name", ""),
            "provider_npi": getattr(claim, "provider_npi", ""),
            "provider_name": getattr(claim, "provider_name", ""),
            "facility_npi": getattr(claim, "facility_npi", ""),
            "date_of_service": getattr(claim, "date_of_service", ""),
            "date_of_birth": getattr(claim, "date_of_birth", ""),
            "place_of_service": getattr(claim, "place_of_service", "11"),
            "items": [
                {
                    "cpt_code": getattr(item, "cpt_code", ""),
                    "cpt_description": getattr(item, "cpt_description", ""),
                    "icd_codes": getattr(item, "icd_codes", []),
                    "modifiers": getattr(item, "modifiers", []),
                    "units": getattr(item, "units", 1),
                    "charge_amount": getattr(item, "charge_amount", 0.0),
                    "place_of_service": getattr(item, "place_of_service", "11"),
                    "diagnosis_pointers": getattr(item, "diagnosis_pointers", []),
                }
                for item in (getattr(claim, "items", []) or [])
            ],
            "total_charges": getattr(claim, "total_charges", 0.0),
            "claim_type": getattr(claim, "claim_type", "professional"),
        }

    def _extract_diagnosis_codes(self, c: Dict) -> List[str]:
        """Extract unique diagnosis codes from claim items."""
        seen = []
        for item in c.get("items", []):
            icd_codes = item.get("icd_codes", []) if isinstance(item, dict) else []
            for code in icd_codes:
                if code and code not in seen:
                    seen.append(code)
        return seen

    def _format_diagnosis_pointers(self, diagnosis_codes: List[str]) -> List[Dict]:
        """Format diagnosis codes for Box 21."""
        return [
            {"pointer": i + 1, "code": code}
            for i, code in enumerate(diagnosis_codes)
        ]

    def _format_line_items(
        self, items: List[Dict], diagnosis_codes: List[str]
    ) -> List[Dict[str, Any]]:
        """Format line items for Box 24 (a-j)."""
        formatted = []
        for item in items:
            item_dict = item if isinstance(item, dict) else {}
            pointers = item_dict.get("diagnosis_pointers", [])
            if not pointers:
                pointers = list(range(1, min(len(diagnosis_codes) + 1, 4)))

            formatted.append({
                "24a_date_of_service": item_dict.get("date_of_service", ""),
                "24b_place_of_service": item_dict.get("place_of_service", "11"),
                "24c_emergency": "",
                "24d_cpt_hcpcs": item_dict.get("cpt_code", ""),
                "24e_modifiers": item_dict.get("modifiers", []),
                "24f_diagnosis_pointers": pointers,
                "24g_charges": item_dict.get("charge_amount", 0.0),
                "24h_units": item_dict.get("units", 1),
                "24i_epsdt": "",
                "24j_rendering_npi": "",
            })
        return formatted

    def _map_insurance_type(self, payer_name: str) -> str:
        """Map payer name to insurance type code for Box 1."""
        payer_upper = payer_name.upper() if payer_name else ""
        if "MEDICARE" in payer_upper:
            return "MB"
        elif "MEDICAID" in payer_upper:
            return "MC"
        elif "BLUE" in payer_upper or "BCBS" in payer_upper:
            return "BL"
        elif "TRICARE" in payer_upper or "CHAMPVA" in payer_upper:
            return "CH"
        elif "WORKERS" in payer_upper or "COMP" in payer_upper:
            return "WC"
        return "CI"

    def export_pdf_ready(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export CMS-1500 data in a PDF-ready format
        with positioned text blocks for form rendering.
        """
        boxes = form_data.get("boxes", {})
        positioned = {
            "form_type": "CMS-1500",
            "version": form_data.get("version", "02/12"),
            "page": 1,
            "render_blocks": [],
        }

        box_positions = {
            "1": {"x": 30, "y": 60, "w": 40, "h": 15},
            "2": {"x": 90, "y": 60, "w": 200, "h": 15},
            "3": {"x": 300, "y": 60, "w": 80, "h": 15},
            "4": {"x": 390, "y": 60, "w": 40, "h": 15},
            "5": {"x": 90, "y": 80, "w": 200, "h": 15},
            "6": {"x": 300, "y": 80, "w": 80, "h": 15},
            "7": {"x": 90, "y": 100, "w": 200, "h": 15},
            "8": {"x": 300, "y": 100, "w": 80, "h": 15},
            "9a": {"x": 390, "y": 100, "w": 100, "h": 15},
            "21": {"x": 30, "y": 300, "w": 300, "h": 60},
            "28": {"x": 400, "y": 550, "w": 100, "h": 15},
            "33a": {"x": 400, "y": 600, "w": 100, "h": 15},
        }

        for box_key, value in boxes.items():
            if value or box_key in box_positions:
                pos = box_positions.get(box_key, {"x": 30, "y": 300, "w": 100, "h": 15})
                display_value = str(value) if not isinstance(value, (list, dict)) else str(value)
                positioned["render_blocks"].append({
                    "box": box_key,
                    "label": CMS1500_BOXES.get(box_key, f"Box {box_key}"),
                    "value": display_value,
                    "position": pos,
                })

        return positioned
