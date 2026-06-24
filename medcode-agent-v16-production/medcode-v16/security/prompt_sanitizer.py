"""
Prompt Sanitizer — Phase 9 Security Architecture

Sanitizes prompts before they reach the LLM.
Removes or neutralizes dangerous content while preserving clinical meaning.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SanitizationResult:
    """Result of prompt sanitization."""
    sanitized: str = ""
    original: str = ""
    removed_count: int = 0
    neutralized_count: int = 0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sanitized_length": len(self.sanitized),
            "original_length": len(self.original),
            "removed_count": self.removed_count,
            "neutralized_count": self.neutralized_count,
        }


class PromptSanitizer:
    """
    Sanitizes prompts by removing/neutralizing dangerous content.

    Operations:
    1. Remove instruction override attempts
    2. Neutralize role-switching commands
    3. Strip encoded malicious payloads
    4. Remove excessive delimiters
    5. Normalize boundaries
    """

    # Patterns to remove entirely
    REMOVE_PATTERNS = [
        r"(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:previous|above|prior|system)\s+(?:instructions|directions|prompts|commands)",
        r"(?:reveal|show|leak|dump|expose)\s+(?:your|the|system|hidden|secret)\s+(?:prompt|instructions|system\s+message)",
        r"<\|im_start\|>\s*system",
        r"<\|im_end\|>",
    ]

    # Patterns to neutralize (replace with safe alternatives)
    NEUTRALIZE_MAP = {
        r"you\s+are\s+now\s+(?:a\s+)?": "Current context: ",
        r"from\s+now\s+on\s+": "Additionally, ",
        r"act\s+as\s+(?:if\s+)?(?:you\s+are\s+)?": "Consider this scenario: ",
        r"pretend\s+(?:you\s+are|that|to\s+be)": "Consider ",
        r"\bsystem\s+prompt\b": "instructions",
        r"\byour\s+system\s+instructions\b": "the guidelines",
    }

    # Dangerous patterns that should always be removed
    DANGEROUS_PATTERNS = {
        "bypass_security": r"bypass\s+(?:safety|security|restrictions|content\s+policy|all\s+rules)",
        "extract_data": r"(?:extract|leak|steal|exfiltrate)\s+(?:all|every|any)\s+(?:patient|medical|clinical|personal)\s+(?:data|records|information)",
        "override_compliance": r"(?:ignore|disable|turn\s+off)\s+(?:compliance|audit|logging|monitoring)",
    }

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def sanitize(self, prompt: str) -> SanitizationResult:
        """
        Sanitize a prompt for LLM submission.

        Args:
            prompt: Raw prompt text.

        Returns:
            SanitizationResult with safe prompt.
        """
        if not prompt:
            return SanitizationResult(original=prompt, sanitized=prompt)

        original = prompt
        sanitized = prompt
        removed = 0
        neutralized = 0
        warnings: List[str] = []

        # Step 1: Remove dangerous patterns
        for attack_type, pattern in self.DANGEROUS_PATTERNS.items():
            found = re.findall(pattern, sanitized, re.IGNORECASE)
            if found:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
                removed += len(found)
                warnings.append(f"Removed dangerous pattern: {attack_type}")

        # Step 2: Remove instruction override/leak patterns
        for pattern in self.REMOVE_PATTERNS:
            found = re.findall(pattern, sanitized, re.IGNORECASE)
            if found:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
                removed += len(found)

        # Step 3: Neutralize role-switching and boundary patterns
        for pattern, replacement in self.NEUTRALIZE_MAP.items():
            compiled = re.compile(pattern, re.IGNORECASE)
            matches = compiled.findall(sanitized)
            if matches:
                sanitized = compiled.sub(replacement, sanitized)
                neutralized += len(matches)

        # Step 4: Remove excessive repeated delimiters (potential injection)
        sanitized = re.sub(r"[-=_*]{10,}", "[---]", sanitized)

        # Step 5: Strip trailing/leading whitespace from removals
        sanitized = re.sub(r"\s{3,}", "  ", sanitized)
        sanitized = sanitized.strip()

        return SanitizationResult(
            sanitized=sanitized,
            original=original,
            removed_count=removed,
            neutralized_count=neutralized,
            warnings=warnings,
        )

    def sanitize_for_log(self, text: str) -> str:
        """
        Quick sanitize for log-safe output.
        Removes only the most dangerous patterns.
        """
        for attack_type, pattern in self.DANGEROUS_PATTERNS.items():
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
        return text.strip()
