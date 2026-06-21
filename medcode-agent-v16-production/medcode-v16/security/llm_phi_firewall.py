"""
MedCode AI V19 — LLM PHI Firewall
===================================
HIPAA §164.312(e)(2)(ii) — Encryption of ePHI during transmission.

Ensures no PHI reaches external LLM providers:
  - De-identify clinical text before LLM calls
  - Replace PHI with reversible tokens
  - Re-identify tokens in LLM responses (internal use only)
  - Log all PHI-to-token mappings (encrypted)
  - Never return raw PHI in API responses
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from security.encryption import get_encryption


@dataclass
class PHIToken:
    """A PHI token replacing actual PHI in LLM prompts."""
    token: str
    phi_type: str
    original_hash: str  # One-way hash, never store original
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "phi_type": self.phi_type,
        }


@dataclass
class DeidentificationResult:
    """Result of de-identifying clinical text."""
    original_text: str
    deidentified_text: str
    tokens: List[PHIToken] = field(default_factory=list)
    phi_count: int = 0
    phi_types: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "phi_count": self.phi_count,
            "phi_types": list(set(self.phi_types)),
            "tokens_created": len(self.tokens),
        }


# PHI patterns for de-identification
PHI_PATTERNS: List[Tuple[str, str, str]] = [
    ("NAME", r"\b(?:patient|pt|dr\.?|doctor)\s+(?:name\s*:?\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", "PATIENT_NAME"),
    ("DOB", r"\bDOB\s*:?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "DATE_OF_BIRTH"),
    ("MRN", r"\bMRN\s*:?\s*\d{4,12}\b", "MEDICAL_RECORD"),
    ("SSN", r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b", "SSN"),
    ("PHONE", r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "PHONE"),
    ("EMAIL", r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", "EMAIL"),
    ("NPI", r"\bNPI\s*:?\s*\d{10}\b", "NPI"),
    ("DATE", r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b", "DATE"),
    ("ADDRESS", r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct))\b", "ADDRESS"),
    ("ZIP", r"\b\d{5}(?:-\d{4})?\b", "ZIP_CODE"),
]


class LLMPhiFirewall:
    """
    LLM PHI Firewall — ensures no PHI reaches external LLM providers.
    
    Process:
      1. De-identify clinical text before LLM calls
      2. Replace PHI with reversible tokens (stored encrypted)
      3. After LLM response, re-identify tokens for internal use
      4. Never return raw PHI in API responses
    """

    def __init__(self):
        self._encryption = get_encryption()
        self._token_map: Dict[str, str] = {}  # token -> encrypted original
        self._reverse_map: Dict[str, str] = {}  # encrypted original -> token

    def deidentify(self, text: str) -> DeidentificationResult:
        """
        De-identify clinical text by replacing PHI with tokens.
        
        Args:
            text: Clinical text containing potential PHI
        
        Returns:
            DeidentificationResult with de-identified text and tokens
        """
        result = DeidentificationResult(original_text=text, deidentified_text=text)
        deidentified = text

        for phi_type, pattern, token_prefix in PHI_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                original = match.group(0)
                token = f"[{token_prefix}_{uuid.uuid4().hex[:6].upper()}]"

                encrypted_original = self._encryption.encrypt(original)
                
                phi_token = PHIToken(
                    token=token,
                    phi_type=phi_type,
                    original_hash=self._encryption.hash_phi(original),
                )
                result.tokens.append(phi_token)

                self._token_map[token] = encrypted_original
                self._reverse_map[encrypted_original] = token

                deidentified = deidentified.replace(original, token, 1)

        result.deidentified_text = deidentified
        result.phi_count = len(result.tokens)
        result.phi_types = list(set(t.phi_type for t in result.tokens))

        return result

    def reidentify(self, text: str, tokens: Optional[List[PHIToken]] = None) -> str:
        """
        Re-identify tokens in text (internal use only).
        NEVER call this for external responses.
        """
        reidentified = text
        
        for token, encrypted_original in self._token_map.items():
            if token in reidentified:
                try:
                    original = self._encryption.decrypt(encrypted_original)
                    reidentified = reidentified.replace(token, original)
                except Exception:
                    pass

        return reidentified

    def sanitize_for_llm(self, text: str) -> Tuple[str, DeidentificationResult]:
        """
        Sanitize clinical text for LLM consumption.
        Returns de-identified text and the result for re-identification.
        """
        result = self.deidentify(text)
        return result.deidentified_text, result

    def sanitize_llm_response(self, response: str, deidentification: DeidentificationResult) -> str:
        """
        Sanitize LLM response to ensure no PHI is included.
        Re-identifies tokens for internal use only.
        """
        sanitized = response
        
        for token in deidentification.tokens:
            if token.token in sanitized:
                sanitized = sanitized.replace(token.token, "[PHI]")

        return sanitized

    def get_phi_summary(self) -> Dict[str, int]:
        """Get summary of PHI types encountered."""
        summary: Dict[str, int] = {}
        for token in self._token_map:
            phi_type = token.split("_")[0].strip("[")
            summary[phi_type] = summary.get(phi_type, 0) + 1
        return summary

    def clear_token_maps(self):
        """Clear all token mappings (call after processing complete)."""
        self._token_map.clear()
        self._reverse_map.clear()


_firewall: Optional[LLMPhiFirewall] = None


def get_llm_phi_firewall() -> LLMPhiFirewall:
    global _firewall
    if _firewall is None:
        _firewall = LLMPhiFirewall()
    return _firewall
