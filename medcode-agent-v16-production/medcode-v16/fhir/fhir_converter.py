"""
FHIR Converter — convert between FHIR R4 resources and MedCode internal data.
"""

import base64
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class FHIRConverter:
    """Bidirectional converter between FHIR R4 resources and MedCode data."""

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _meta(resource_type: str, resource_id: str) -> dict:
        return {
            "resourceType": resource_type,
            "id": resource_id,
            "meta": {"lastUpdated": FHIRConverter._now()},
        }

    def clinical_note_from_document(self, doc_ref: dict) -> str:
        """Extract clinical note text from a FHIR DocumentReference."""
        for attachment in doc_ref.get("content", []):
            att = attachment.get("attachment", {})
            if att.get("contentType", "").startswith("text/"):
                data = att.get("data")
                if data:
                    return base64.b64decode(data).decode("utf-8")
                url = att.get("url")
                if url:
                    return f"[Attachment URL: {url}]"
        for att in doc_ref.get("content", []):
            a = att.get("attachment", {})
            data = a.get("data")
            if data:
                return base64.b64decode(data).decode("utf-8")
        text = doc_ref.get("text", {}).get("div", "")
        if text:
            import re
            return re.sub(r"<[^>]+>", "", text)
        return ""

    def observation_to_code(self, observation: dict) -> dict:
        """Convert a FHIR Observation to a coding suggestion dict."""
        coding_list = observation.get("code", {}).get("coding", [{}])
        code_obj = coding_list[0] if coding_list else {}
        loinc = code_obj.get("code", "")
        display = code_obj.get("display", "")
        value = None
        if "valueQuantity" in observation:
            value = observation["valueQuantity"].get("value")
        elif "valueString" in observation:
            value = observation["valueString"]
        elif "valueCodeableConcept" in observation:
            vcc = observation["valueCodeableConcept"]
            value = vcc.get("coding", [{}])[0].get("display", vcc.get("text", ""))
        return {
            "system": code_obj.get("system", "http://loinc.org"),
            "code": loinc,
            "display": display,
            "value": value,
            "status": observation.get("status", "unknown"),
            "effective_date": observation.get("effectiveDateTime", ""),
            "source": "fhir_observation",
        }

    def condition_to_icd(self, condition: dict) -> dict:
        """Convert a FHIR Condition to an ICD-10 coding dict."""
        coding_list = (
            condition.get("code", {}).get("coding", [{}])
        )
        icd_coding = next(
            (
                c
                for c in coding_list
                if "icd" in c.get("system", "").lower()
            ),
            coding_list[0] if coding_list else {},
        )
        clinical_status = condition.get("clinicalStatus", {})
        status_coding = (
            clinical_status.get("coding", [{}])[0]
            if isinstance(clinical_status, dict)
            else {}
        )
        return {
            "system": icd_coding.get("system", "http://hl7.org/fhir/sid/icd-10-cm"),
            "code": icd_coding.get("code", ""),
            "display": icd_coding.get("display", ""),
            "clinical_status": status_coding.get("code", "unknown"),
            "verification_status": (
                condition.get("verificationStatus", {})
                .get("coding", [{}])[0]
                .get("code", "unknown")
            ),
            "onset": condition.get("onsetDateTime", ""),
            "source": "fhir_condition",
        }

    def procedure_to_cpt(self, procedure: dict) -> dict:
        """Convert a FHIR Procedure to a CPT coding dict."""
        coding_list = (
            procedure.get("code", {}).get("coding", [{}])
        )
        cpt_coding = next(
            (
                c
                for c in coding_list
                if "cpt" in c.get("system", "").lower()
            ),
            coding_list[0] if coding_list else {},
        )
        status = procedure.get("status", "unknown")
        return {
            "system": cpt_coding.get(
                "system", "http://www.ama-assn.org/go/cpt"
            ),
            "code": cpt_coding.get("code", ""),
            "display": cpt_coding.get("display", ""),
            "status": status,
            "performed_date": procedure.get(
                "performedDateTime",
                (
                    procedure.get("performedPeriod", {}).get("start", "")
                ),
            ),
            "source": "fhir_procedure",
        }

    def coding_result_to_bundle(self, codes: dict) -> dict:
        """Convert MedCode coding results to a FHIR Bundle of ClaimItem entries."""
        entries: list[dict] = []
        timestamp = self._now()
        for i, cpt in enumerate(codes.get("cpt_codes", []), 1):
            entries.append(
                {
                    "fullUrl": f"urn:uuid:cpt-{i}",
                    "resource": {
                        "resourceType": "ClaimItem",
                        "id": f"item-cpt-{i}",
                        "meta": {"lastUpdated": timestamp},
                        "category": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/claim-category",
                                    "code": "professional",
                                }
                            ]
                        },
                        "code": {
                            "coding": [
                                {
                                    "system": "http://www.ama-assn.org/go/cpt",
                                    "code": cpt.get("code", "") if isinstance(cpt, dict) else str(cpt),
                                    "display": cpt.get("display", "") if isinstance(cpt, dict) else "",
                                }
                            ]
                        },
                    },
                    "request": {
                        "method": "POST",
                        "url": "ClaimItem",
                    },
                }
            )
        for i, icd in enumerate(codes.get("icd_codes", []), 1):
            entries.append(
                {
                    "fullUrl": f"urn:uuid:icd-{i}",
                    "resource": {
                        "resourceType": "Condition",
                        "id": f"condition-icd-{i}",
                        "meta": {"lastUpdated": timestamp},
                        "code": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                    "code": icd.get("code", "") if isinstance(icd, dict) else str(icd),
                                    "display": icd.get("display", "") if isinstance(icd, dict) else "",
                                }
                            ]
                        },
                    },
                    "request": {
                        "method": "POST",
                        "url": "Condition",
                    },
                }
            )
        return {
            "resourceType": "Bundle",
            "id": "medcode-coding-result",
            "meta": {"lastUpdated": timestamp},
            "type": "collection",
            "timestamp": timestamp,
            "total": len(entries),
            "entry": entries,
        }

    def patient_from_resource(self, patient_resource: dict) -> dict:
        """Extract patient demographics from a FHIR Patient resource."""
        name_entries = patient_resource.get("name", [{}])
        name_obj = name_entries[0] if name_entries else {}
        given = name_obj.get("given", [])
        family = name_obj.get("family", "")
        telecom = patient_resource.get("telecom", [])
        phone = next(
            (
                t.get("value")
                for t in telecom
                if t.get("system") == "phone"
            ),
            "",
        )
        email = next(
            (
                t.get("value")
                for t in telecom
                if t.get("system") == "email"
            ),
            "",
        )
        return {
            "id": patient_resource.get("id", ""),
            "family_name": family,
            "given_name": " ".join(given),
            "birth_date": patient_resource.get("birthDate", ""),
            "gender": patient_resource.get("gender", ""),
            "phone": phone,
            "email": email,
            "address": self._extract_address(patient_resource),
            "mrn": self._extract_mrn(patient_resource),
        }

    @staticmethod
    def _extract_address(patient: dict) -> str:
        addresses = patient.get("address", [])
        if not addresses:
            return ""
        addr = addresses[0]
        parts = [
            addr.get("line", [""])[0] if addr.get("line") else "",
            addr.get("city", ""),
            addr.get("state", ""),
            addr.get("postalCode", ""),
        ]
        return ", ".join(p for p in parts if p)

    @staticmethod
    def _extract_mrn(patient: dict) -> str:
        for ident in patient.get("identifier", []):
            system = ident.get("system", "")
            if "mrn" in system.lower() or "medical-record" in system.lower():
                return ident.get("value", "")
        identifiers = patient.get("identifier", [])
        if identifiers:
            return identifiers[0].get("value", "")
        return ""
