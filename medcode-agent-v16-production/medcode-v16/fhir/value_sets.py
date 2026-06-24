"""
FHIR ValueSets — wraps the MedCode book engines for CPT and ICD-10-CM codes
and exposes them as FHIR-compatible ValueSet operations.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FHIRValueSetManager:
    """FHIR ValueSet operations backed by MedCode's CPT and ICD-10 book engines."""

    def __init__(self):
        self._cpt_engine = None
        self._icd_engine = None

    def _get_cpt_engine(self):
        if self._cpt_engine is None:
            try:
                from knowledge.cpt_book_engine import CPTBookEngine
                self._cpt_engine = CPTBookEngine()
            except Exception as exc:
                logger.warning("CPT book engine unavailable: %s", exc)
                self._cpt_engine = False
        return self._cpt_engine

    def _get_icd_engine(self):
        if self._icd_engine is None:
            try:
                from knowledge.icd_book_engine import ICDBookEngine
                self._icd_engine = ICDBookEngine()
            except Exception as exc:
                logger.warning("ICD book engine unavailable: %s", exc)
                self._icd_engine = False
        return self._icd_engine

    def expand_value_set(
        self, code_system: str, filter_text: str = "", max_results: int = 100
    ) -> list[dict]:
        """Expand a FHIR ValueSet by code system name with optional text filter."""
        system = code_system.lower()
        if system in ("cpt", "cpt-4"):
            return self._expand_cpt(filter_text, max_results)
        elif system in ("icd10", "icd-10", "icd-10-cm"):
            return self._expand_icd(filter_text, max_results)
        return []

    def _expand_cpt(self, filter_text: str, max_results: int) -> list[dict]:
        engine = self._get_cpt_engine()
        if not engine:
            return []
        if filter_text:
            try:
                results = engine.search_cpt(filter_text)
            except Exception:
                results = []
        else:
            try:
                results = engine.get_em_codes()
                if len(results) < max_results:
                    surgery = engine.get_surgery_codes()
                    results.extend(surgery)
            except Exception:
                results = []
        output = []
        for code in results[:max_results]:
            if isinstance(code, dict):
                output.append({
                    "code": code.get("code", ""),
                    "desc": code.get("desc", ""),
                    "display": code.get("desc", ""),
                    "system": "http://www.ama-assn.org/go/cpt",
                    "status": "active",
                })
            elif isinstance(code, str):
                info = engine.lookup_cpt(code) if engine else None
                output.append({
                    "code": code,
                    "desc": info.get("desc", "") if info else "",
                    "display": info.get("desc", "") if info else "",
                    "system": "http://www.ama-assn.org/go/cpt",
                    "status": "active",
                })
        return output

    def _expand_icd(self, filter_text: str, max_results: int) -> list[dict]:
        engine = self._get_icd_engine()
        if not engine:
            return []
        if filter_text:
            try:
                results = engine.search_icd(filter_text)
            except Exception:
                results = []
        else:
            try:
                results = engine.get_chapter_codes("IX")
                for ch in range(1, 22):
                    if len(results) >= max_results:
                        break
                    try:
                        chapter_codes = engine.get_chapter_codes(str(ch))
                        results.extend(chapter_codes)
                    except Exception:
                        pass
            except Exception:
                results = []
        output = []
        for code in results[:max_results]:
            if isinstance(code, dict):
                output.append({
                    "code": code.get("code", ""),
                    "desc": code.get("desc", ""),
                    "display": code.get("desc", ""),
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "status": "active",
                    "billable": code.get("billable", True),
                })
            elif isinstance(code, str):
                info = engine.lookup_icd(code) if engine else None
                output.append({
                    "code": code,
                    "desc": info.get("desc", "") if info else "",
                    "display": info.get("desc", "") if info else "",
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "status": "active",
                    "billable": info.get("billable", True) if info else True,
                })
        return output

    def validate_code(
        self, code_system: str, code_value: str
    ) -> dict:
        """Validate a code against a ValueSet ($validate-code operation)."""
        system = code_system.lower()
        if system in ("cpt", "cpt-4"):
            return self._validate_cpt(code_value)
        elif system in ("icd10", "icd-10", "icd-10-cm"):
            return self._validate_icd(code_value)
        return {
            "result": False,
            "message": f"Unknown code system: {code_system}",
        }

    def _validate_cpt(self, code: str) -> dict:
        engine = self._get_cpt_engine()
        if not engine:
            return {"result": False, "message": "CPT engine unavailable"}
        try:
            info = engine.lookup_cpt(code)
            if info:
                return {
                    "result": True,
                    "display": info.get("desc", ""),
                    "system": "http://www.ama-assn.org/go/cpt",
                }
        except Exception as exc:
            logger.debug("CPT validation error: %s", exc)
        return {"result": False, "message": f"CPT code {code} not found"}

    def _validate_icd(self, code: str) -> dict:
        engine = self._get_icd_engine()
        if not engine:
            return {"result": False, "message": "ICD engine unavailable"}
        try:
            info = engine.lookup_icd(code)
            if info:
                return {
                    "result": True,
                    "display": info.get("desc", ""),
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "billable": info.get("billable", True),
                }
        except Exception as exc:
            logger.debug("ICD validation error: %s", exc)
        return {"result": False, "message": f"ICD-10 code {code} not found"}

    def get_value_set_metadata(self, code_system: str) -> dict:
        """Return FHIR ValueSet resource metadata."""
        system = code_system.lower()
        if system in ("cpt", "cpt-4"):
            return {
                "resourceType": "ValueSet",
                "id": "cpt-codes",
                "url": "http://medcode.ai/fhir/ValueSet/cpt",
                "version": "2026",
                "name": "CPTCodes",
                "title": "CPT Procedure Codes",
                "status": "active",
                "publisher": "MedCode AI",
                "description": "Current Procedural Terminology (CPT) codes for medical procedure coding",
                "copyright": "American Medical Association",
                "compose": {
                    "include": [
                        {
                            "system": "http://www.ama-assn.org/go/cpt",
                            "version": "2026",
                        }
                    ]
                },
            }
        elif system in ("icd10", "icd-10", "icd-10-cm"):
            return {
                "resourceType": "ValueSet",
                "id": "icd-10-cm-codes",
                "url": "http://medcode.ai/fhir/ValueSet/icd-10-cm",
                "version": "2026",
                "name": "ICD10CMCodes",
                "title": "ICD-10-CM Diagnosis Codes",
                "status": "active",
                "publisher": "MedCode AI",
                "description": "International Classification of Diseases, 10th Revision, Clinical Modification",
                "copyright": "World Health Organization / CMS",
                "compose": {
                    "include": [
                        {
                            "system": "http://hl7.org/fhir/sid/icd-10-cm",
                            "version": "2026",
                        }
                    ]
                },
            }
        return {
            "resourceType": "ValueSet",
            "id": "unknown",
            "status": "active",
            "compose": {"include": []},
        }
