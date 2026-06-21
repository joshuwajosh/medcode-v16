"""
Base Reasoner — MedCode AI V17/V19
====================================
Shared infrastructure for all 16 specialty reasoners.
Provides:
  - ReasonedCode dataclass (scored code with reasoning chain)
  - ReasoningResult dataclass (aggregate reasoner output)
  - SpecialtyReasoner base class with shared helpers
  - REASONER_REGISTRY for dynamic lookup
  - Module-level convenience functions
  
V19: Added HIPAA-compliant audit trail per decision.
"""

from __future__ import annotations
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ReasonedCode:
    """
    A single code (CPT or ICD) produced by a specialty reasoner.
    Contains the full reasoning chain and confidence score.
    """
    code: str
    description: str
    confidence: float          # 0.0–100.0
    reasoning: List[str]       # Step-by-step reasoning chain
    guidelines: List[str]      # References to CPT/CMS guidelines
    code_type: str = "CPT"     # "CPT", "ICD", "HCPCS", "Modifier"
    modifiers: List[str] = field(default_factory=list)
    specialty: str = ""
    section: str = ""
    subsection: str = ""
    anatomy: str = ""
    approach: str = ""
    is_add_on: bool = False
    global_period_days: int = 0

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "description": self.description,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "guidelines": self.guidelines,
            "code_type": self.code_type,
            "modifiers": self.modifiers,
            "specialty": self.specialty,
            "section": self.section,
            "subsection": self.subsection,
            "anatomy": self.anatomy,
            "approach": self.approach,
            "is_add_on": self.is_add_on,
            "global_period_days": self.global_period_days,
        }


@dataclass
class ReasoningResult:
    """
    Full output from a specialty reasoner for a given clinical note/question.
    V19: Added audit trail for HIPAA compliance.
    """
    specialty: str
    primary_code: Optional[ReasonedCode] = None
    secondary_codes: List[ReasonedCode] = field(default_factory=list)
    icd_codes: List[ReasonedCode] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    extraction: Dict[str, Any] = field(default_factory=dict)
    guidelines_applied: List[str] = field(default_factory=list)
    confidence_overall: float = 0.0
    processing_time_ms: float = 0.0
    requires_review: bool = False
    review_reason: str = ""
    error: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "specialty": self.specialty,
            "primary_code": self.primary_code.to_dict() if self.primary_code else None,
            "secondary_codes": [c.to_dict() for c in self.secondary_codes],
            "icd_codes": [c.to_dict() for c in self.icd_codes],
            "modifiers": self.modifiers,
            "reasoning_chain": self.reasoning_chain,
            "extraction": self.extraction,
            "guidelines_applied": self.guidelines_applied,
            "confidence_overall": self.confidence_overall,
            "processing_time_ms": self.processing_time_ms,
            "requires_review": self.requires_review,
            "review_reason": self.review_reason,
            "error": self.error,
            "audit_trail": self.audit_trail,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Base Reasoner Class
# ─────────────────────────────────────────────────────────────────────────────

class SpecialtyReasoner:
    """
    Abstract base for all 16 specialty reasoners.

    Subclasses MUST define:
      - specialty_name: str        (e.g., "Cardiovascular")
      - cpt_families: list         (e.g., ["cabg_arterial", "cabg_venous", ...])
      - keywords: list             (trigger terms for this specialty)
      - code_hierarchies: dict     (family -> {code -> (description, rules)})

    Subclasses SHOULD override:
      - extract_procedure(note)    → dict of extracted details
      - reason(note, extraction)   → ReasoningResult
      - _score_code(code, ctx)     → confidence float
      - validate_ncci(code, codes) → bool

    Shared helpers provided:
      - _has(note, *terms)         → bool (case-insensitive substring)
      - _extract_number(note, pattern) → Optional[float]
      - _extract_count(note, word) → Optional[int]
      - _build_chain(*steps)       → list of reasoning steps
    """

    specialty_name: str = "General"
    cpt_families: List[str] = []
    keywords: List[str] = []
    code_hierarchies: Dict[str, Dict[str, Any]] = {}
    section: str = "Surgery"
    global_period_default: int = 90

    def __init__(self, specialty: Optional[str] = None, cpt_families: Optional[Dict[str, Dict[str, str]]] = None):
        self._name_re = re.compile(r'\b([A-Za-z]+)\b')
        self._number_re = re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:cm|mm|mg|mcg|ml|hours?|min(?:utes?)?|grafts?|lesions?|units?|view(?:s)?)?\b', re.IGNORECASE)
        self.code_lookup: Dict[str, Dict[str, Any]] = {}
        if specialty is not None:
            self.specialty_name = specialty
        if cpt_families is not None:
            self.cpt_families = cpt_families

    # ── Shared Helpers ───────────────────────────────────────────────────────

    def _has(self, text: str, *terms: str) -> bool:
        """Case-insensitive substring match for any of the terms."""
        t = text.lower()
        return any(term.lower() in t for term in terms)

    def _all_has(self, text: str, *terms: str) -> bool:
        """All terms must match."""
        t = text.lower()
        return all(term.lower() in t for term in terms)

    def _extract_number(self, text: str, pattern: str = r'(\d+(?:\.\d+)?)') -> Optional[float]:
        """Extract first number matching pattern."""
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
        return None

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text."""
        return [float(m.group(1)) for m in self._number_re.finditer(text)]

    def _extract_count(self, text: str, word: str = "graft") -> Optional[int]:
        """Extract count like '3 arterial grafts' or 'three grafts' or '4+ grafts'."""
        # Digit patterns
        patterns = [
            rf'(\d+)\+?\s*(?:arterial|venous|saphenous|vein)?\s*{word}s?',
            rf'{word}s?\s*[×x]\s*(\d+)',
            rf'{word}s?.*?(\d+)',
            rf'(\d+)\s*{word}s?',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return int(m.group(1))
        # Word patterns
        word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                     "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        for w, n in word_map.items():
            if re.search(rf'\b{w}\s*(?:arterial|venous|saphenous|vein)?\s*{word}s?\b', text, re.IGNORECASE):
                return n
        return None

    def _build_chain(self, *steps: str) -> List[str]:
        """Build reasoning chain from step strings."""
        return [s for s in steps if s]

    def _make_code(self, code: str, desc: str, conf: float, chain: List[str],
                   guidelines: Optional[List[str]] = None, **kwargs) -> ReasonedCode:
        return ReasonedCode(
            code=code, description=desc, confidence=conf,
            reasoning=chain, guidelines=guidelines or [],
            specialty=self.specialty_name, section=self.section,
            **kwargs
        )

    def _capped(self, score: float) -> float:
        return max(0.0, min(100.0, score))

    # ── Override Points ──────────────────────────────────────────────────────

    def extract_procedure(self, note: str) -> Dict[str, Any]:
        """
        Extract procedure details from clinical text.
        Returns dict with keys like: procedure, anatomy, approach, intent, device, etc.
        """
        return {"raw_text": note}

    def reason(self, note: str, extraction: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """
        Main reasoning entry point.
        Must be overridden by subclasses to produce specialty-specific reasoning.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement reason()")

    def run(self, note: str) -> ReasoningResult:
        """Public API: extract + reason with timing and audit trail."""
        start = time.time()
        try:
            extraction = self.extract_procedure(note)
            result = self.reason(note, extraction)
            result.extraction = extraction
            result.specialty = self.specialty_name
            
            result.audit_trail.append({
                "stage": "extraction",
                "status": "complete",
                "specialty": self.specialty_name,
                "timestamp": time.time(),
            })
            
            if result.primary_code:
                result.audit_trail.append({
                    "stage": "code_selection",
                    "status": "complete",
                    "code": result.primary_code.code,
                    "confidence": result.primary_code.confidence,
                    "timestamp": time.time(),
                })
            
            result.audit_trail.append({
                "stage": "reasoning_complete",
                "status": "complete",
                "codes_generated": len(result.secondary_codes) + (1 if result.primary_code else 0),
                "requires_review": result.requires_review,
                "timestamp": time.time(),
            })
            
        except Exception as e:
            result = ReasoningResult(
                specialty=self.specialty_name,
                error=str(e),
                requires_review=True,
                review_reason=f"Reasoner exception: {e}",
                audit_trail=[{
                    "stage": "error",
                    "status": "failed",
                    "error": str(e),
                    "timestamp": time.time(),
                }],
            )
        result.processing_time_ms = round((time.time() - start) * 1000, 1)
        return result

    def validate_ncci(self, codes: List[str]) -> List[str]:
        """Return violations or empty list. Override for specialty-specific NCCI."""
        return []

    def get_global_period(self, code: str) -> int:
        """Return global period in days for a code. Default 90 for surgery, 0 for E/M etc."""
        return self.global_period_default

    # ── Error Result ─────────────────────────────────────────────────────────

    def _review_required(self, reason: str) -> ReasoningResult:
        return ReasoningResult(
            specialty=self.specialty_name,
            requires_review=True,
            review_reason=reason,
        )


# Backwards-compatible alias
BaseSpecialtyReasoner = SpecialtyReasoner


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

REASONER_REGISTRY: Dict[str, SpecialtyReasoner] = {}
# REASONER_CLASS_REGISTRY for class-based lookup
REASONER_CLASS_REGISTRY: Dict[str, type] = {}


def register_reasoner(reasoner: SpecialtyReasoner):
    """Register a reasoner instance by its specialty name."""
    name = reasoner.specialty_name.lower().replace(" ", "_")
    REASONER_REGISTRY[name] = reasoner


def get_reasoner(specialty: str) -> Optional[SpecialtyReasoner]:
    """Get a reasoner by specialty name (case-insensitive)."""
    key = specialty.lower().replace(" ", "_").replace("/", "_")
    return REASONER_REGISTRY.get(key)


def get_all_reasoners() -> List[SpecialtyReasoner]:
    """Get all registered reasoners."""
    return list(REASONER_REGISTRY.values())


def reason_all(note: str, specialties: Optional[List[str]] = None) -> Dict[str, ReasoningResult]:
    """
    Run all (or specified) reasoners on a note.
    Returns dict of specialty_name -> ReasoningResult.
    """
    if specialties:
        reasoners = [get_reasoner(s) for s in specialties if get_reasoner(s)]
    else:
        reasoners = get_all_reasoners()
    results = {}
    for r in reasoners:
        results[r.specialty_name] = r.run(note)
    return results


def reason_specialty(note: str, specialty: str) -> Optional[ReasoningResult]:
    """Run a single specialty reasoner."""
    reasoner = get_reasoner(specialty)
    if reasoner:
        return reasoner.run(note)
    return None
