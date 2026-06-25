
"""
CDI (Clinical Documentation Improvement) Engine V17.
Detects documentation gaps: unspecified diagnoses, missing acuity/severity/stage,
incomplete operative reports, missing laterality.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import re


@dataclass
class CDIOpportunity:
    category: str
    severity: str  # high, medium, low
    description: str
    evidence: str
    recommendation: str
    query_suggestion: str


UNSPECIFIED_PATTERNS = [
    (r"unspecified", "Unspecified term used"),
    (r"not otherwise specified", "NOS term used"),
    (r"NEC", "Not elsewhere classifiable"),
    (r"not specified", "Not specified"),
    (r"unknown etiology", "Unknown etiology"),
    (r"other\s+\w+\s+(of|without)", "Other specified category"),
]

MISSING_ACUITY_KEYWORDS = [
    "acute", "chronic", "subacute", "acute-on-chronic",
    "mild", "moderate", "severe", "critical"
]

MISSING_SEVERITY_KEYWORDS = [
    "stage", "grade", "class", "type", "severity"
]

WEAK_DOC_PATTERNS = [
    (r"(?:appears|seems|likely|probably|possibly|maybe|suspected|\\?)",
     "Uncertain language - may affect coding specificity"),
    (r"(?:history\s+of|hx\s+of|past\s+medical\s+history)\s+\w+",
     "Historical condition - requires clarification of active status"),
    (r"reported",
     "Patient reported without clinical confirmation"),
    (r"denies?",
     "Negative finding - ensure appropriately documented"),
]


class CDIEngine:
    """Deterministic CDI opportunity detection engine."""

    def __init__(self):
        pass

    def analyze(self, note_text: str, cpt_codes: List[str],
                icd_codes: List[str]) -> List[CDIOpportunity]:
        opportunities = []
        text_lower = note_text.lower()

        # 1. Detect unspecified diagnoses
        for pattern, desc in UNSPECIFIED_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                opportunities.append(CDIOpportunity(
                    category="unspecified_diagnosis",
                    severity="high",
                    description=f"Unspecified term: '{match.group()}'",
                    evidence=match.group(),
                    recommendation=f"Replace '{match.group()}' with a more specific diagnosis",
                    query_suggestion=f"Please specify the type/etiology of the condition described as '{match.group()}'"
                ))

        # 2. Check for missing acuity
        for code in icd_codes:
            has_acuity = any(kw in text_lower for kw in MISSING_ACUITY_KEYWORDS)
            if not has_acuity and self._is_condition_requiring_acuity(code):
                opportunities.append(CDIOpportunity(
                    category="missing_acuity",
                    severity="high",
                    description=f"ICD-10 {code}: Missing acuity (acute/chronic)",
                    evidence=f"ICD-10 code {code} requires acuity specification",
                    recommendation="Add acute/chronic/acute-on-chronic qualifier",
                    query_suggestion=f"Is the condition coded as {code} acute, chronic, or acute-on-chronic?"
                ))

        # 3. Check for missing severity/stage/grade
        for code in icd_codes:
            if self._is_severity_required(code):
                has_severity = any(
                    re.search(rf"{kw}\s+\d", text_lower)
                    for kw in MISSING_SEVERITY_KEYWORDS
                )
                if not has_severity:
                    opportunities.append(CDIOpportunity(
                        category="missing_severity",
                        severity="high",
                        description=f"ICD-10 {code}: Missing severity/stage/grade",
                        evidence=f"ICD-10 code {code} typically requires stage or grade",
                        recommendation="Document stage, grade, or severity level",
                        query_suggestion=f"Please document the stage, grade, or severity for condition coded as {code}"
                    ))

        # 4. Check for missing laterality
        for code in icd_codes:
            if self._is_laterality_required(code):
                if not re.search(r"(left|right|bilateral|unilateral)", text_lower):
                    opportunities.append(CDIOpportunity(
                        category="missing_laterality",
                        severity="medium",
                        description=f"ICD-10 {code}: Missing laterality",
                        evidence=f"ICD-10 code {code} typically requires left/right/bilateral specification",
                        recommendation="Add laterality (left/right/bilateral)",
                        query_suggestion=f"Please indicate laterality (left, right, or bilateral) for condition coded as {code}"
                    ))

        # 5. Detect weak documentation language
        for pattern, desc in WEAK_DOC_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                opportunities.append(CDIOpportunity(
                    category="weak_documentation",
                    severity="medium",
                    description=desc,
                    evidence=f"Found: '{match.group()}'",
                    recommendation="Provide definitive clinical language",
                    query_suggestion="Please clarify the definitive diagnosis based on clinical findings"
                ))

        # 6. Check for incomplete operative report
        if self._is_operative_note(note_text):
            missing_elements = []
            if not re.search(r"(?:pre-op|preoperative|pre-op diagnosis)", text_lower):
                missing_elements.append("pre-operative diagnosis")
            if not re.search(r"(?:post-op|postoperative|post-op diagnosis)", text_lower):
                missing_elements.append("post-operative diagnosis")
            if not re.search(r"(?:estimated blood loss|ebl|blood loss)", text_lower):
                missing_elements.append("estimated blood loss")
            if not re.search(r"(?:complication|no complication|unremarkable|uneventful)", text_lower):
                missing_elements.append("complication status")
            if not re.search(r"(?:specimen|pathology|sent to pathology)", text_lower):
                missing_elements.append("specimen disposition")

            if missing_elements:
                for element in missing_elements:
                    opportunities.append(CDIOpportunity(
                        category="incomplete_operative_report",
                        severity="medium",
                        description=f"Missing operative report element: {element}",
                        evidence=f"Could not find documentation of {element}",
                        recommendation=f"Document {element} in operative report",
                        query_suggestion=f"Please document the {element} in the operative report"
                    ))

        return opportunities

    def _is_condition_requiring_acuity(self, code: str) -> bool:
        prefix = code.split(".")[0] if "." in code else code
        acuity_required = [
            "I50", "N17", "N18", "J44", "J45", "J96",
            "E10", "E11", "E87", "K70", "K71",
        ]
        return any(prefix.startswith(p) for p in acuity_required)

    def _is_severity_required(self, code: str) -> bool:
        prefix = code.split(".")[0] if "." in code else code
        severity_required = [
            "C50", "C61", "C18", "C34", "C43",
            "L89", "D25", "M17", "M16",
            "I48", "N18", "K74", "J44",
        ]
        return any(prefix.startswith(p) for p in severity_required)

    def _is_laterality_required(self, code: str) -> bool:
        prefix = code.split(".")[0] if "." in code else code
        laterality_required = ["C50", "M17", "M16", "H25", "H40", "S42", "S72", "S82"]
        return any(prefix.startswith(p) for p in laterality_required)

    def _is_operative_note(self, note_text: str) -> bool:
        indicators = ["procedure", "surgery", "operation", "operative",
                      "incision", "excision", "resection", "repair"]
        return any(ind in note_text.lower() for ind in indicators)


def analyze_cdi_opportunities(note_text: str, cpt_codes: List[str] = None,
                              icd_codes: List[str] = None) -> dict:
    """Pipeline integration for CDI analysis."""
    engine = CDIEngine()
    opportunities = engine.analyze(note_text, cpt_codes or [], icd_codes or [])
    return {
        "cdi_opportunities": [
            {
                "category": o.category,
                "severity": o.severity,
                "description": o.description,
                "evidence": o.evidence,
                "recommendation": o.recommendation,
                "query_suggestion": o.query_suggestion,
            }
            for o in opportunities
        ],
        "total_opportunities": len(opportunities),
        "high_priority": sum(1 for o in opportunities if o.severity == "high"),
        "medium_priority": sum(1 for o in opportunities if o.severity == "medium"),
        "overall_documentation_risk": self._calculate_risk(opportunities),
    }


def _calculate_risk(opportunities):
    if not opportunities:
        return "low"
    high_count = sum(1 for o in opportunities if o.severity == "high")
    if high_count >= 3:
        return "high"
    if high_count >= 1:
        return "moderate"
    return "low"
