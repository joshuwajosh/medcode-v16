"""
MedCode AI — EDI 837 Claim File Generation
============================================
Generates HIPAA-compliant 837P (professional) and
837I (institutional) electronic claim files.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
import time


# EDI delimiters per HIPAA X12 5010 specification
ELEMENT_SEPARATOR = "*"
COMPOSITE_SEPARATOR = ":"
SEGMENT_TERMINATOR = "~"
NEWLINE = "\r\n"

# ISA segment fixed positions
ISA_QUALIFIERS = {
    "ZZ": "Mutually Defined",
    "MI": "Medicare ID",
    "XX": "National Provider Identifier",
}

# Payer identification qualifier
PAYER_QUALIFIER = "PI"


class EDI837Generator:
    """
    Generates HIPAA-compliant EDI 837 files for
    professional (837P) and institutional (837I) claims.
    """

    def __init__(self):
        self.interchange_control_number = 0
        self.group_control_number = 0
        self.transaction_set_control_number = 0

    def generate_837p(self, claim) -> Dict[str, Any]:
        """
        Generate EDI 837P (professional claim) file content.

        Args:
            claim: Claim dataclass or dict with claim fields.

        Returns:
            Dict with edi_content (string), metadata, and segment_count.
        """
        c = self._to_dict(claim)
        self._increment_counters()

        segments = []

        # ISA segment (Interchange Control Header)
        segments.append(self._isa_segment())

        # GS segment (Functional Group Header)
        segments.append(self._gs_segment())

        # ST segment (Transaction Set Header - 837P = 837)
        segments.append(self._st_segment("837"))

        # BHT segment (Beginning of Hierarchical Transaction)
        segments.append(self._bht_segment())

        # 1000A: Submitter Name
        segments.extend(self._loop_1000a_submitter(c))

        # 1000B: Receiver Name
        segments.extend(self._loop_1000b_receiver(c))

        # 2000A: Billing Provider Hierarchical Level
        segments.extend(self._loop_2000a_billing_provider(c))

        # 2010AA: Billing Provider Name
        segments.extend(self._loop_2010aa_billing_provider_name(c))

        # 2000B: Subscriber Hierarchical Level
        segments.extend(self._loop_2000b_subscriber(c))

        # 2010BA: Subscriber Name
        segments.extend(self._loop_2010ba_subscriber_name(c))

        # 2010BB: Payer Name
        segments.extend(self._loop_2010bb_payer_name(c))

        # 2300: Claim Information
        segments.extend(self._loop_2300_claim_info(c))

        # 2400: Service Line
        for item in c.get("items", []):
            item_dict = item if isinstance(item, dict) else {}
            segments.extend(self._loop_2400_service_line(item_dict, c))

        # SE segment (Transaction Set Trailer)
        segment_count = len(segments) - 2  # exclude ISA and GS
        segments.append(self._se_segment(segment_count))

        # GE segment (Functional Group Trailer)
        segments.append(self._ge_segment())

        # ISE segment (Interchange Control Trailer)
        segments.append(self._ise_segment())

        edi_content = NEWLINE.join(segments)

        return {
            "edi_type": "837P",
            "edi_content": edi_content,
            "segment_count": len(segments),
            "claim_id": c.get("claim_id", ""),
            "payer_name": c.get("payer_name", ""),
            "total_charges": c.get("total_charges", 0.0),
            "generated_at": datetime.utcnow().isoformat(),
            "isa_control_number": self.interchange_control_number,
            "gs_control_number": self.group_control_number,
            "st_control_number": self.transaction_set_control_number,
        }

    def generate_837i(self, claim) -> Dict[str, Any]:
        """
        Generate EDI 837I (institutional claim) file content.

        Args:
            claim: Claim dataclass or dict with claim fields.

        Returns:
            Dict with edi_content (string), metadata, and segment_count.
        """
        c = self._to_dict(claim)
        self._increment_counters()

        segments = []

        # ISA segment
        segments.append(self._isa_segment())

        # GS segment
        segments.append(self._gs_segment())

        # ST segment (837I = 837)
        segments.append(self._st_segment("837"))

        # BHT segment
        segments.append(self._bht_segment())

        # 1000A: Submitter Name
        segments.extend(self._loop_1000a_submitter(c))

        # 1000B: Receiver Name
        segments.extend(self._loop_1000b_receiver(c))

        # 2000A: Billing Provider Hierarchical Level
        segments.extend(self._loop_2000a_billing_provider(c))

        # 2010AA: Billing Provider Name
        segments.extend(self._loop_2010aa_billing_provider_name(c))

        # 2000B: Subscriber Hierarchical Level
        segments.extend(self._loop_2000b_subscriber(c))

        # 2010BA: Subscriber Name
        segments.extend(self._loop_2010ba_subscriber_name(c))

        # 2010BB: Payer Name
        segments.extend(self._loop_2010bb_payer_name(c))

        # 2300: Claim Information (institutional format)
        segments.extend(self._loop_2300_claim_info(c))

        # 2400: Service Line with Revenue Codes
        for item in c.get("items", []):
            item_dict = item if isinstance(item, dict) else {}
            segments.extend(self._loop_2400i_service_line_institutional(item_dict, c))

        # SE segment
        segment_count = len(segments) - 2
        segments.append(self._se_segment(segment_count))

        # GE segment
        segments.append(self._ge_segment())

        # ISE segment
        segments.append(self._ise_segment())

        edi_content = NEWLINE.join(segments)

        return {
            "edi_type": "837I",
            "edi_content": edi_content,
            "segment_count": len(segments),
            "claim_id": c.get("claim_id", ""),
            "payer_name": c.get("payer_name", ""),
            "total_charges": c.get("total_charges", 0.0),
            "generated_at": datetime.utcnow().isoformat(),
            "isa_control_number": self.interchange_control_number,
            "gs_control_number": self.group_control_number,
            "st_control_number": self.transaction_set_control_number,
        }

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

    def _increment_counters(self):
        """Increment EDI control numbers."""
        self.interchange_control_number += 1
        self.group_control_number += 1
        self.transaction_set_control_number += 1

    def _e(self, *elements) -> str:
        """Join elements with the element separator."""
        return ELEMENT_SEPARATOR.join(str(e) for e in elements)

    def _seg(self, *elements) -> str:
        """Build a complete segment with terminator."""
        return self._e(*elements) + SEGMENT_TERMINATOR

    def _isa_segment(self) -> str:
        """ISA - Interchange Control Header."""
        now = datetime.now()
        date_str = now.strftime("%y%m%d")
        time_str = now.strftime("%H%M")
        icn = str(self.interchange_control_number).zfill(9)

        return self._seg(
            "ISA",
            "00",
            "          ",
            "00",
            "          ",
            "ZZ",
            "MEDCODESENDER    ",
            "ZZ",
            "PAYERRECEIVER    ",
            date_str,
            time_str,
            "^",
            "00501",
            icn,
            "0",
            "P",
            ":",
        )

    def _gs_segment(self) -> str:
        """GS - Functional Group Header."""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        gn = str(self.group_control_number)

        return self._seg(
            "GS",
            "HC",
            "MEDCODE",
            "PAYER",
            date_str,
            time_str,
            gn,
            "X",
            "005010X222A1",
        )

    def _st_segment(self, transaction_id: str) -> str:
        """ST - Transaction Set Header."""
        return self._seg(
            "ST",
            transaction_id,
            str(self.transaction_set_control_number).zfill(4),
        )

    def _bht_segment(self) -> str:
        """BHT - Beginning of Hierarchical Transaction."""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        return self._seg(
            "BHT",
            "0019",
            "00",
            f"CLM{self.transaction_set_control_number}",
            date_str,
            "",
            "CH",
        )

    def _loop_1000a_submitter(self, c: Dict) -> List[str]:
        """1000A: Submitter Name."""
        return [
            self._seg("NM1", "41", "2", "MEDCODE AI", "", "", "", "46", "MEDCODE"),
            self._seg("PER", "IC", "SUPPORT", "TE", "5551234567"),
        ]

    def _loop_1000b_receiver(self, c: Dict) -> List[str]:
        """1000B: Receiver Name."""
        payer = c.get("payer_name", "PAYER")
        payer_id = payer.upper().replace(" ", "")[:15]
        return [
            self._seg("NM1", "40", "2", payer, "", "", "", "46", payer_id),
        ]

    def _loop_2000a_billing_provider(self, c: Dict) -> List[str]:
        """2000A: Billing Provider Hierarchical Level."""
        return [
            self._seg("HL", "1", "", "20", "1"),
            self._seg("PRV", "BI", "PXC", "208100000X"),
        ]

    def _loop_2010aa_billing_provider_name(self, c: Dict) -> List[str]:
        """2010AA: Billing Provider Name."""
        provider = c.get("provider_name", "PROVIDER")
        npi = c.get("provider_npi", "")
        parts = provider.split(", ") if ", " in provider else [provider, ""]
        last = parts[0] if parts else ""
        first = parts[1] if len(parts) > 1 else ""

        return [
            self._seg("NM1", "85", "2", last, first, "", "", "XX", npi),
            self._seg("N3", "123 Medical Center Dr"),
            self._seg("N4", "Anytown", "CA", "90210"),
            self._seg("REF", "EI", npi),
        ]

    def _loop_2000b_subscriber(self, c: Dict) -> List[str]:
        """2000B: Subscriber Hierarchical Level."""
        return [
            self._seg("HL", "2", "1", "22", "0"),
        ]

    def _loop_2010ba_subscriber_name(self, c: Dict) -> List[str]:
        """2010BA: Subscriber Name."""
        patient = c.get("patient_name", "PATIENT")
        parts = patient.split(", ") if ", " in patient else [patient, ""]
        last = parts[0] if parts else ""
        first = parts[1] if len(parts) > 1 else ""
        ins_id = c.get("insurance_id", "")
        dob = c.get("patient_dob", c.get("date_of_birth", "")).replace("-", "")
        sex_code = self._map_sex(c.get("patient_sex", ""))

        return [
            self._seg("NM1", "IL", "1", last, first, "", "", "MI", ins_id),
            self._seg("N3", "456 Patient St"),
            self._seg("N4", "Anytown", "CA", "90210"),
            self._seg("DMG", "D8", dob, sex_code),
            self._seg("REF", "SY", ins_id),
        ]

    def _loop_2010bb_payer_name(self, c: Dict) -> List[str]:
        """2010BB: Payer Name."""
        payer = c.get("payer_name", "PAYER")
        payer_id = payer.upper().replace(" ", "")[:15]
        return [
            self._seg("NM1", "PR", "2", payer, "", "", "", "PI", payer_id),
            self._seg("N3", "Payer Address"),
            self._seg("N4", "Payer City", "ST", "00000"),
        ]

    def _loop_2300_claim_info(self, c: Dict) -> List[str]:
        """2300: Claim Information."""
        claim_id = c.get("claim_id", "")
        dos = c.get("date_of_service", "").replace("-", "")
        pos = c.get("place_of_service", "11")
        total = c.get("total_charges", 0.0)
        frequency = "1"  # Original claim

        claim_id_qualifier = "D9"

        segs = [
            self._seg(
                "CLM",
                f"*{claim_id}",
                f"{total}:N",
                f"{frequency}",
                "",
                f"{pos}",
                "",
                "Y",
                "A",
                "Y",
                "Y",
            ),
        ]

        # DTM - Date/Time Reference
        if dos:
            segs.append(self._seg("DTM", "431", dos))
            segs.append(self._seg("DTM", "454", dos))

        # Diagnosis codes
        diagnosis_codes = self._extract_diagnosis_codes(c)
        if diagnosis_codes:
            diag_str = "".join(f":{code}:9" for code in diagnosis_codes)
            segs.append(self._seg("HI", f"ABK:{diagnosis_codes[0]}"))

        # REF - Claim Number
        segs.append(self._seg("REF", "D9", claim_id))

        return segs

    def _loop_2400_service_line(self, item: Dict, c: Dict) -> List[str]:
        """2400: Service Line (professional)."""
        cpt = item.get("cpt_code", "")
        modifiers = item.get("modifiers", [])
        charge = item.get("charge_amount", 0.0)
        units = item.get("units", 1)
        dos = c.get("date_of_service", "").replace("-", "")
        pointers = item.get("diagnosis_pointers", [])

        service_id = self._e("HC", cpt)
        if modifiers:
            for mod in modifiers[:4]:
                service_id += f":{mod}"

        segs = [
            self._seg("LX", str(item.get("line_number", 1))),
            self._seg(
                "SV1",
                service_id,
                f"{charge}",
                "UN",
                str(units),
                "",
                "",
                "",
            ),
        ]

        if dos:
            segs.append(self._seg("DTP", "472", "D8", dos))

        if pointers:
            diag_str = self._e(*pointers)
            segs.append(self._seg("CR1", "", "", "", "", "", diag_str))

        return segs

    def _loop_2400i_service_line_institutional(self, item: Dict, c: Dict) -> List[str]:
        """2400: Service Line (institutional with revenue codes)."""
        cpt = item.get("cpt_code", "")
        charge = item.get("charge_amount", 0.0)
        units = item.get("units", 1)
        dos = c.get("date_of_service", "").replace("-", "")
        pos = item.get("place_of_service", "21")

        revenue_code = self._map_cpt_to_revenue(cpt)

        segs = [
            self._seg("LX", str(item.get("line_number", 1))),
            self._seg(
                "SV2",
                revenue_code,
                f":{charge}",
                "UN",
                str(units),
                "",
                "",
            ),
        ]

        if dos:
            segs.append(self._seg("DTP", "472", "D8", dos))

        return segs

    def _se_segment(self, segment_count: int) -> str:
        """SE - Transaction Set Trailer."""
        return self._seg(
            "SE",
            segment_count,
            str(self.transaction_set_control_number).zfill(4),
        )

    def _ge_segment(self) -> str:
        """GE - Functional Group Trailer."""
        return self._seg("GE", "1", str(self.group_control_number))

    def _ise_segment(self) -> str:
        """IEA - Interchange Control Trailer."""
        return self._seg(
            "IEA",
            "1",
            str(self.interchange_control_number).zfill(9),
        )

    def _extract_diagnosis_codes(self, c: Dict) -> List[str]:
        """Extract unique diagnosis codes from claim items."""
        seen = []
        for item in c.get("items", []):
            icd_codes = item.get("icd_codes", []) if isinstance(item, dict) else []
            for code in icd_codes:
                if code and code not in seen:
                    seen.append(code)
        return seen

    def _map_sex(self, sex: str) -> str:
        """Map sex description to EDI code."""
        sex_upper = sex.upper() if sex else ""
        if sex_upper in ("M", "MALE"):
            return "M"
        elif sex_upper in ("F", "FEMALE"):
            return "F"
        return "U"

    def _map_cpt_to_revenue(self, cpt_code: str) -> str:
        """Map a CPT code to a revenue center code."""
        if cpt_code.startswith("992"):
            return "0130"
        elif cpt_code.startswith("993"):
            return "0200"
        elif cpt_code.startswith("97"):
            return "0600"
        elif cpt_code.startswith("8"):
            return "0300"
        elif cpt_code.startswith("7"):
            return "0400"
        return "0990"
