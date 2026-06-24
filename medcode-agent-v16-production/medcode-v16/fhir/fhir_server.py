"""
FHIR R4 Server — expose MedCode AI capabilities as FHIR-compatible endpoints.
Serves FHIR resources with proper resourceType, id, meta.lastUpdated structure.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class FHIRServer:
    """FHIR R4 server that wraps MedCode AI's coding capabilities."""

    def __init__(self):
        self.converter = None
        self._init_converter()

    def _init_converter(self):
        try:
            from fhir.fhir_converter import FHIRConverter
            self.converter = FHIRConverter()
        except ImportError:
            logger.warning("FHIRConverter unavailable, server in degraded mode")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _meta(resource_type: str, resource_id: str) -> dict:
        return {
            "resourceType": resource_type,
            "id": resource_id,
            "meta": {"lastUpdated": FHIRServer._now()},
        }

    def _operation_outcome(
        self,
        issues: list[dict],
        severity: str = "error",
        code: str = "processing",
    ) -> dict:
        return {
            "resourceType": "OperationOutcome",
            "id": "outcome-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "meta": {"lastUpdated": self._now()},
            "issue": [
                {
                    "severity": issue.get("severity", severity),
                    "code": issue.get("code", code),
                    "diagnostics": issue.get("diagnostics", ""),
                }
                for issue in issues
            ],
        }

    def get_patient(self, patient_id: str) -> dict:
        return {
            **self._meta("Patient", patient_id),
            "identifier": [
                {
                    "system": "http://medcode.ai/fhir/mrn",
                    "value": f"MRN-{patient_id}",
                }
            ],
            "name": [
                {
                    "use": "official",
                    "family": "Patient",
                    "given": [f"Test{patient_id}"],
                }
            ],
            "gender": "unknown",
            "birthDate": "2000-01-01",
        }

    def get_encounter(self, encounter_id: str) -> dict:
        return {
            **self._meta("Encounter", encounter_id),
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "270427003",
                            "display": "Patient encounter",
                        }
                    ]
                }
            ],
        }

    def get_document_reference(self, doc_id: str) -> dict:
        return {
            **self._meta("DocumentReference", doc_id),
            "status": "current",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "34133-9",
                        "display": "Summarization of Episode Note",
                    }
                ]
            },
            "content": [
                {
                    "attachment": {
                        "contentType": "text/plain",
                        "language": "en",
                    }
                }
            ],
        }

    def get_document_references_for_patient(self, patient_id: str) -> dict:
        timestamp = self._now()
        return {
            "resourceType": "Bundle",
            "id": f"docs-{patient_id}",
            "meta": {"lastUpdated": timestamp},
            "type": "searchset",
            "timestamp": timestamp,
            "total": 0,
            "entry": [],
            "link": [
                {
                    "relation": "self",
                    "url": f"/fhir/DocumentReference?patient={patient_id}",
                }
            ],
        }

    def get_concept_expand(
        self,
        code_system: str,
        filter_text: Optional[str] = None,
    ) -> dict:
        from fhir.value_sets import FHIRValueSetManager
        manager = FHIRValueSetManager()
        system = "cpt" if "cpt" in code_system.lower() else "icd10"
        results = manager.expand_value_set(system, filter_text or "")
        timestamp = self._now()
        return {
            "resourceType": "ValueSet",
            "id": f"expand-{system}",
            "meta": {"lastUpdated": timestamp},
            "status": "active",
            "expansion": {
                "timestamp": timestamp,
                "total": len(results),
                "contains": [
                    {
                        "system": (
                            "http://www.ama-assn.org/go/cpt"
                            if system == "cpt"
                            else "http://hl7.org/fhir/sid/icd-10-cm"
                        ),
                        "code": r.get("code", ""),
                        "display": r.get("desc", r.get("display", "")),
                    }
                    for r in results[:50]
                ],
            },
        }

    def get_value_set(
        self,
        value_set_id: str,
        filter_text: Optional[str] = None,
    ) -> dict:
        from fhir.value_sets import FHIRValueSetManager
        manager = FHIRValueSetManager()
        system = "cpt" if "cpt" in value_set_id.lower() else "icd10"
        results = manager.expand_value_set(system, filter_text or "")
        timestamp = self._now()
        system_url = (
            "http://www.ama-assn.org/go/cpt"
            if system == "cpt"
            else "http://hl7.org/fhir/sid/icd-10-cm"
        )
        return {
            "resourceType": "ValueSet",
            "id": value_set_id,
            "meta": {"lastUpdated": timestamp},
            "url": f"http://medcode.ai/fhir/ValueSet/{value_set_id}",
            "status": "active",
            "expansion": {
                "timestamp": timestamp,
                "total": len(results),
                "contains": [
                    {
                        "system": system_url,
                        "code": r.get("code", ""),
                        "display": r.get("desc", r.get("display", "")),
                    }
                    for r in results
                ],
            },
        }

    def create_document_reference(
        self, clinical_note: str, patient_id: str = "unknown"
    ) -> dict:
        import base64
        encoded = base64.b64encode(clinical_note.encode("utf-8")).decode("utf-8")
        doc_id = f"doc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return {
            **self._meta("DocumentReference", doc_id),
            "status": "current",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "34133-9",
                        "display": "Summarization of Episode Note",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "content": [
                {
                    "attachment": {
                        "contentType": "text/plain",
                        "language": "en",
                        "data": encoded,
                        "size": len(clinical_note),
                        "title": f"Clinical Note - {patient_id}",
                    }
                }
            ],
        }
