"""
MedCode AI — UB-04 (Institutional Claim) Form Generation
==========================================================
Generates structured JSON data mapping UB-04 fields
for institutional claim PDF rendering and EDI transmission.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# UB-04 field descriptions
UB04_FIELDS = {
    "field_01": "Provider Name",
    "field_02": "Provider Address",
    "field_03": "Provider City, State, ZIP",
    "field_04": "Provider Tax ID",
    "field_05": "Reserved",
    "field_06": "Pay-to Name and Address",
    "field_07": "Pay-to City, State, ZIP",
    "field_08": "Patient Control Number",
    "field_09": "Medical Record Number",
    "field_10": "Type of Bill",
    "field_11": "Federal Tax ID",
    "field_12": "Patient Identifier",
    "field_13": "Patient Name",
    "field_14": "Patient Birth Date",
    "field_15": "Patient Sex",
    "field_16": "Admission Date",
    "field_17a": "Admission Hour",
    "field_17b": "Point of Origin",
    "field_17c": "Source",
    "field_18": "Discharge Hour",
    "field_19": "Patient Status",
    "field_20": "Condition Code",
    "field_21": "Occurrence Code",
    "field_22": "Occurrence Span Code",
    "field_23": "Occurrence Span Dates",
    "field_24a": "Revenue Code",
    "field_24b": "Revenue Description",
    "field_24c": "HCPCS/Rate",
    "field_24d": "Service Date",
    "field_24e": "Service Units",
    "field_24f": "Service Charges",
    "field_24g": "Non-Covered Charges",
    "field_25": "Reserved",
    "field_26": "Reserved",
    "field_27": "Reserved",
    "field_28": "Reserved",
    "field_29": "Reserved",
    "field_30": "Reserved",
    "field_31": "Reserved",
    "field_32": "Reserved",
    "field_33": "Reserved",
    "field_34": "Reserved",
    "field_35": "Reserved",
    "field_36": "Reserved",
    "field_37": "Reserved",
    "field_38": "Reserved",
    "field_39": "Reserved",
    "field_40": "Reserved",
    "field_41": "Reserved",
    "field_42": "Reserved",
    "field_43": "Reserved",
    "field_44": "Reserved",
    "field_45": "Reserved",
    "field_46": "Reserved",
    "field_47": "Reserved",
    "field_48": "Reserved",
    "field_49": "Reserved",
    "field_50": "Reserved",
    "field_51": "Reserved",
    "field_52": "Reserved",
    "field_53": "Reserved",
    "field_54": "Reserved",
    "field_55": "Reserved",
    "field_56": "Reserved",
    "field_57": "Reserved",
    "field_58": "Reserved",
    "field_59": "Reserved",
    "field_60": "Reserved",
    "field_61": "Reserved",
    "field_62": "Reserved",
    "field_63": "Reserved",
    "field_64": "Reserved",
    "field_65": "Reserved",
    "field_66": "Reserved",
    "field_67": "Reserved",
    "field_68": "Reserved",
    "field_69": "Reserved",
    "field_70": "Reserved",
    "field_71": "Reserved",
    "field_72": "Reserved",
    "field_73": "Reserved",
    "field_74": "Reserved",
    "field_75": "Reserved",
    "field_76": "Reserved",
    "field_77": "Reserved",
    "field_78": "Reserved",
    "field_79": "Reserved",
    "field_80": "Reserved",
    "field_81": "Reserved",
    "field_82": "Reserved",
    "field_83": "Reserved",
    "field_84": "Reserved",
    "field_85": "Reserved",
    "field_86": "Reserved",
    "field_87": "Reserved",
    "field_88": "Reserved",
    "field_89": "Reserved",
    "field_90": "Reserved",
    "field_91": "Reserved",
    "field_92": "Reserved",
    "field_93": "Reserved",
    "field_94": "Reserved",
    "field_95": "Reserved",
    "field_96": "Reserved",
    "field_97": "Reserved",
    "field_98": "Reserved",
    "field_99": "Reserved",
    "field_100": "Reserved",
    "field_101": "Reserved",
    "field_102": "Reserved",
    "field_103": "Reserved",
    "field_104": "Reserved",
    "field_105": "Reserved",
    "field_106": "Reserved",
    "field_107": "Reserved",
    "field_108": "Reserved",
    "field_109": "Reserved",
    "field_110": "Reserved",
    "field_111": "Reserved",
    "field_112": "Reserved",
    "field_113": "Reserved",
    "field_114": "Reserved",
    "field_115": "Reserved",
    "field_116": "Reserved",
    "field_117": "Reserved",
    "field_118": "Reserved",
    "field_119": "Reserved",
    "field_120": "Reserved",
    "field_121": "Reserved",
    "field_122": "Reserved",
    "field_123": "Reserved",
    "field_124": "Reserved",
    "field_125": "Reserved",
}

# Revenue center codes (common institutional codes)
REVENUE_CENTER_CODES = {
    "0100": "Room and Board - Semi-Private",
    "0110": "Room and Board - Private",
    "0120": "Room and Board - Ward",
    "0130": "Room and Board - Intensive Care Unit",
    "0140": "Room and Board - Coronary Care",
    "0150": "Room and Board - Pediatrics",
    "0160": "Room and Board - Neonatal",
    "0170": "Room and Board - Psychiatric",
    "0180": "Room and Board - Rehabilitation",
    "0200": "Nursing Services",
    "0201": "Nursing - Registered Nurse",
    "0202": "Nursing - Licensed Practical Nurse",
    "0203": "Nursing - Nursing Aide",
    "0210": "IV Therapy",
    "0220": "Medications",
    "0230": "Medications - Oral",
    "0240": "Medications - Injectable",
    "0250": "Medications - Inhalation",
    "0260": "Medications - Ophthalmic",
    "0270": "Medical Supplies",
    "0271": "Medical Supplies - Durable Medical Equipment",
    "0272": "Medical Supplies - Non-Durable",
    "0300": "Laboratory Services",
    "0301": "Laboratory - Clinical Chemistry",
    "0302": "Laboratory - Hematology",
    "0303": "Laboratory - Microbiology",
    "0304": "Laboratory - Pathology",
    "0305": "Laboratory - Immunology",
    "0400": "Radiology Services",
    "0401": "Radiology - Diagnostic X-Ray",
    "0402": "Radiology - Therapeutic X-Ray",
    "0403": "Radiology - Nuclear Medicine",
    "0404": "Radiology - Radiation Therapy",
    "0405": "Radiology - MRI",
    "0406": "Radiology - CT Scan",
    "0407": "Radiology - Ultrasound",
    "0500": "Operating Room Services",
    "0510": "Anesthesia Services",
    "0520": "Recovery Room",
    "0600": "Physical Therapy",
    "0610": "Occupational Therapy",
    "0620": "Speech-Language Pathology",
    "0630": "Respiratory Therapy",
    "0700": "Emergency Services",
    "0710": "Ambulance Services",
    "0800": "Dialysis Services",
    "0810": "Hematology/Oncology",
    "0820": "Psychiatric Services",
    "0830": "Substance Abuse Services",
    "0840": "Rehabilitation Services",
    "0900": "Other Services",
    "0910": "Dental Services",
    "0920": "Vision Services",
    "0930": "Hearing Services",
    "0940": "Prosthetic Devices",
    "0950": "Home Health Services",
    "0960": "Hospice Services",
    "0970": "Skilled Nursing Services",
    "0980": "Extended Care Services",
    "0990": "Miscellaneous Services",
    "1000": "Blood and Blood Products",
    "1100": "Implants",
    "1200": "Specialty Services",
    "1300": "Epidemiological Services",
    "8999": "Unused Revenue Code",
}

# Type of Bill (TOB) codes for institutional claims
TOB_CODES = {
    "111": "Hospital Inpatient (Medicare Part A)",
    "112": "Hospital Inpatient (Medicare Part B)",
    "113": "Hospital Inpatient (Medicaid)",
    "114": "Hospital Inpatient (Other)",
    "121": "Hospital Outpatient (Medicare Part A)",
    "122": "Hospital Outpatient (Medicare Part B)",
    "123": "Hospital Outpatient (Medicaid)",
    "124": "Hospital Outpatient (Other)",
    "211": "SNF Inpatient (Medicare Part A)",
    "212": "SNF Inpatient (Medicare Part B)",
    "213": "SNF Inpatient (Medicaid)",
    "214": "SNF Inpatient (Other)",
    "311": "Home Health (Medicare Part A)",
    "312": "Home Health (Medicare Part B)",
    "313": "Home Health (Medicaid)",
    "314": "Home Health (Other)",
    "411": "Hospice (Medicare Part A)",
    "412": "Hospice (Medicare Part B)",
    "413": "Hospice (Medicaid)",
    "414": "Hospice (Other)",
    "711": "Critical Access Hospital Inpatient",
    "712": "Critical Access Hospital Outpatient",
}


class UB04Generator:
    """
    Generates UB-04 (institutional claim) form data
    in structured JSON format for PDF rendering.
    """

    def generate(self, claim) -> Dict[str, Any]:
        """
        Generate UB-04 form data from a Claim object or dict.

        Args:
            claim: Claim dataclass or dict with claim fields.

        Returns:
            Dict mapping UB-04 fields to values.
        """
        c = self._to_dict(claim)

        line_items = c.get("items", [])
        diagnosis_codes = self._extract_diagnosis_codes(c)

        form: Dict[str, Any] = {
            "form_type": "UB-04",
            "version": "2024",
            "claim_id": c.get("claim_id", ""),
            "fields": {},
        }

        fields = form["fields"]

        # Field 01: Provider Name
        fields["01"] = c.get("provider_name", "")

        # Field 02-03: Provider Address (not in claim data)
        fields["02"] = ""
        fields["03"] = ""

        # Field 04: Provider Tax ID (not in claim data)
        fields["04"] = ""

        # Field 05: Reserved
        fields["05"] = ""

        # Field 06-07: Pay-to Name and Address
        fields["06"] = c.get("provider_name", "")
        fields["07"] = ""

        # Field 08: Patient Control Number
        fields["08"] = c.get("claim_id", "")

        # Field 09: Medical Record Number
        fields["09"] = ""

        # Field 10: Type of Bill
        fields["10"] = self._determine_tob(c)

        # Field 11: Federal Tax ID
        fields["11"] = ""

        # Field 12: Patient Identifier
        fields["12"] = c.get("insurance_id", "")

        # Field 13: Patient Name
        fields["13"] = c.get("patient_name", "")

        # Field 14: Patient Birth Date
        fields["14"] = c.get("patient_dob", c.get("date_of_birth", ""))

        # Field 15: Patient Sex
        fields["15"] = c.get("patient_sex", "")

        # Field 16: Admission Date
        fields["16"] = c.get("date_of_service", "")

        # Field 17: Admission details
        fields["17a"] = ""
        fields["17b"] = "1"  # Emergency
        fields["17c"] = ""

        # Field 18: Discharge Hour
        fields["18"] = ""

        # Field 19: Patient Status
        fields["19"] = "01"  # Discharged

        # Field 20: Condition Code
        fields["20"] = []

        # Field 21: Occurrence Code
        fields["21"] = []

        # Field 22: Occurrence Span Code
        fields["22"] = ""

        # Field 23: Occurrence Span Dates
        fields["23"] = ""

        # Field 24: Revenue Center Lines
        fields["24"] = self._format_revenue_lines(
            line_items, diagnosis_codes, c
        )

        # Fields 25-125: Reserved
        for i in range(25, 126):
            fields[str(i)] = ""

        # Add summary
        form["summary"] = {
            "total_line_items": len(line_items),
            "total_diagnosis_codes": len(diagnosis_codes),
            "total_charges": c.get("total_charges", 0.0),
            "total_revenue_centers": len(fields.get("24", [])),
            "claim_type": "institutional",
            "type_of_bill": fields["10"],
        }

        return form

    def _to_dict(self, claim) -> Dict[str, Any]:
        """Convert Claim dataclass or dict to dict."""
        if isinstance(claim, dict):
            return claim
        if hasattr(claim, "to_dict"):
            return claim.to_dict()
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
            "place_of_service": getattr(claim, "place_of_service", "21"),
            "items": [
                {
                    "cpt_code": getattr(item, "cpt_code", ""),
                    "cpt_description": getattr(item, "cpt_description", ""),
                    "icd_codes": getattr(item, "icd_codes", []),
                    "modifiers": getattr(item, "modifiers", []),
                    "units": getattr(item, "units", 1),
                    "charge_amount": getattr(item, "charge_amount", 0.0),
                    "place_of_service": getattr(item, "place_of_service", "21"),
                    "diagnosis_pointers": getattr(item, "diagnosis_pointers", []),
                }
                for item in (getattr(claim, "items", []) or [])
            ],
            "total_charges": getattr(claim, "total_charges", 0.0),
            "claim_type": getattr(claim, "claim_type", "institutional"),
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

    def _determine_tob(self, c: Dict) -> str:
        """Determine Type of Bill based on claim data."""
        pos = c.get("place_of_service", "21")
        payer = c.get("payer_name", "").upper() if c.get("payer_name") else ""
        claim_type = c.get("claim_type", "institutional")

        if claim_type == "institutional":
            if pos in ("21", "22"):
                if "MEDICARE" in payer:
                    return "111"
                elif "MEDICAID" in payer:
                    return "113"
                return "114"
            elif pos == "31":
                return "211"
        return "111"

    def _format_revenue_lines(
        self, items: List[Dict], diagnosis_codes: List[str], c: Dict
    ) -> List[Dict[str, Any]]:
        """Format line items as revenue center lines for field 24."""
        lines = []
        for item in items:
            item_dict = item if isinstance(item, dict) else {}
            cpt_code = item_dict.get("cpt_code", "")
            revenue_code = self._map_cpt_to_revenue(cpt_code, item_dict)

            lines.append({
                "field_24a_revenue_code": revenue_code,
                "field_24b_revenue_description": REVENUE_CENTER_CODES.get(revenue_code, ""),
                "field_24c_hcpcs_rate": cpt_code,
                "field_24d_service_date": c.get("date_of_service", ""),
                "field_24e_service_units": item_dict.get("units", 1),
                "field_24f_service_charges": item_dict.get("charge_amount", 0.0),
                "field_24g_non_covered_charges": 0.0,
            })
        return lines

    def _map_cpt_to_revenue(self, cpt_code: str, item: Dict) -> str:
        """Map a CPT code to a revenue center code."""
        pos = item.get("place_of_service", "21")

        if cpt_code.startswith("992"):
            if pos == "23":
                return "0700"
            elif pos in ("21", "22"):
                if cpt_code.startswith("9922"):
                    return "0130"
                return "0120"
            return "0100"
        elif cpt_code.startswith("993"):
            return "0200"
        elif cpt_code.startswith("36"):
            return "1000"
        elif cpt_code.startswith("8"):
            return "0300"
        elif cpt_code.startswith("7"):
            return "0400"
        elif cpt_code.startswith("97"):
            return "0600"
        elif cpt_code.startswith("971"):
            return "0600"
        return "0990"

    def export_pdf_ready(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export UB-04 data in a PDF-ready format
        with positioned text blocks for form rendering.
        """
        fields = form_data.get("fields", {})
        positioned = {
            "form_type": "UB-04",
            "version": form_data.get("version", "2024"),
            "page": 1,
            "render_blocks": [],
        }

        key_fields = ["01", "08", "10", "11", "12", "13", "14", "15", "16", "19", "24"]
        y_offset = 30
        for field_key in key_fields:
            value = fields.get(field_key, "")
            display_value = str(value) if not isinstance(value, (list, dict)) else str(value)
            positioned["render_blocks"].append({
                "field": field_key,
                "label": UB04_FIELDS.get(f"field_{field_key}", f"Field {field_key}"),
                "value": display_value,
                "position": {"x": 30, "y": y_offset, "w": 450, "h": 15},
            })
            y_offset += 20

        return positioned
