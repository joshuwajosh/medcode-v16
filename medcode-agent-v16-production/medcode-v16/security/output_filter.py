"""
Output Filter — Phase 3 Security Architecture

Filters LLM outputs for:
- PHI leakage (patient identifiers in generated text)
- Unsafe content
- Restricted data exposure
- Policy violations

Ensures no PHI leaks through model-generated output.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from privacy.phi_detector import PHIDetector, PHIEntity


@dataclass
class OutputFilterResult:
    """Result of output filtering."""
    filtered_output: str = ""
    original_output: str = ""
    phi_leaks_detected: List[PHIEntity] = field(default_factory=list)
    unsafe_patterns_detected: List[str] = field(default_factory=list)
    leak_count: int = 0
    blocked: bool = False

    def to_dict(self) -> dict:
        return {
            "filtered": len(self.filtered_output),
            "phi_leaks": self.leak_count,
            "unsafe_patterns": len(self.unsafe_patterns_detected),
            "blocked": self.blocked,
        }


class OutputFilter:
    """
    Filters LLM outputs for PHI leaks and unsafe content.

    Detects:
    - Patient names, DOBs, SSNs, phone numbers
    - Medical record numbers
    - Email addresses
    - ICU/PHI-containing codes
    - Hallucinated patient data
    """

    # Restricted ICD code patterns that may indicate PHI leakage
    RESTRICTED_CODE_PATTERNS = [
        r"\b[EeVv]\d{2}\.\d{1,4}\b",  # ICD-10 codes (allow in context)
    ]

    # Hallucination indicators — patterns suggesting fabricated patient data
    HALLUCINATION_INDICATORS = [
        r"\bpatient\s+(?:named|called)\s+[A-Z][a-z]+",
        r"\bMr\.?\s+[A-Z][a-z]+\b(?!\s*(?:Smith|Johnson|generic))",
        r"\bMs\.?\s+[A-Z][a-z]+\b(?!\s*(?:Smith|Johnson|generic))",
        r"\bDr\.?\s+[A-Z][a-z]+\b",
    ]

    # Unsafe content patterns
    UNSAFE_PATTERNS = [
        r"bypass",
        r"ignore\s+(?:safety|security|compliance)",
        r"this\s+is\s+(?:not\s+)?(?:medical\s+)?advice",
    ]

    def __init__(self, phi_detector: Optional[PHIDetector] = None,
                 strict_mode: bool = True):
        self.phi_detector = phi_detector or PHIDetector()
        self.strict_mode = strict_mode

    def filter(self, output: str, context: Optional[str] = None) -> OutputFilterResult:
        """
        Filter LLM output for PHI leaks and unsafe content.

        Args:
            output: Raw LLM output text.
            context: Original clinical context for comparison (optional).

        Returns:
            OutputFilterResult with filtered output and leak details.
        """
        if not output:
            return OutputFilterResult(original_output=output, filtered_output=output)

        # Step 1: Scan for PHI in output
        phi_entities = self.phi_detector.detect(output)

        # Step 2: Detect unsafe patterns
        unsafe_pats: List[str] = []
        for pattern in self.UNSAFE_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                unsafe_pats.append(pattern)

        # Step 3: Detect hallucinated patient data
        for pattern in self.HALLUCINATION_INDICATORS:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                unsafe_pats.append(f"hallucinated_patient_data: {matches[0][:40]}")

        # Step 4: Filter (redact leaked PHI)
        filtered = output
        for entity in phi_entities:
            placeholder = f"[LEAKED_{entity.phi_type.upper()}]"
            filtered = filtered.replace(entity.text, placeholder)

        # Step 5: Block if too many leaks
        blocked = False
        if self.strict_mode and len(phi_entities) > 3:
            blocked = True
            filtered = "[OUTPUT BLOCKED — PHI LEAK DETECTED]"

        return OutputFilterResult(
            filtered_output=filtered,
            original_output=output,
            phi_leaks_detected=phi_entities,
            unsafe_patterns_detected=unsafe_pats,
            leak_count=len(phi_entities),
            blocked=blocked,
        )

    def is_safe(self, output: str) -> bool:
        """Quick check: is the output safe?"""
        result = self.filter(output)
        return result.leak_count == 0 and not result.blocked and len(result.unsafe_patterns_detected) == 0
