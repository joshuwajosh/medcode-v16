"""
Instruction Guard — Phase 9 Security Architecture

Protects system instructions from being leaked or overridden.
Maintains instruction hierarchy: system > user > agent.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GuardResult:
    """Result of instruction guard check."""
    protected: bool = True
    instruction_leak_detected: bool = False
    instruction_override_detected: bool = False
    risk_score: float = 0.0
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "protected": self.protected,
            "leak_detected": self.instruction_leak_detected,
            "override_detected": self.instruction_override_detected,
            "risk_score": self.risk_score,
            "detail_count": len(self.details),
        }


class InstructionGuard:
    """
    Protects system instructions from leakage and override attempts.

    Maintains instruction hierarchy:
    - System instructions (highest priority, immutable by user)
    - Pipeline instructions (set by orchestrator)
    - User/agent instructions (constrained by system & pipeline)
    """

    # Patterns indicating instruction leak attempts
    LEAK_PATTERNS = [
        r"(?:what|show|tell|reveal).{0,30}(?:instruction|prompt|system|role)",
        r"(?:your|the)\s+(?:initial|original|first|system)\s+(?:instruction|prompt|message|directive)",
        r"(?:repeat|say|echo|list)\s+(?:your|the)\s+(?:system|instruction|prompt)",
        r"(?:print|output|display|show|write)\s+(?:your|the)\s+(?:system|full|complete|entire)\s+(?:prompt|instruction)",
    ]

    # Patterns indicating override attempts
    OVERRIDE_PATTERNS = [
        r"(?:ignore|override|disregard|forget|bypass)\s+(?:your|all|the|system|previous)",
        r"(?:new|updated|modified)\s+(?:instruction|command|rule|directive)",
        r"you\s+(?:must|should|will|have\s+to)\s+(?:now|instead|actually)",
        r"(?:from|starting)\s+(?:now|here|this\s+point)\s+(?:on|forward)",
        r"don'?t\s+(?:follow|obey|listen)",
    ]

    def __init__(self, system_instructions: Optional[str] = None,
                 strict_mode: bool = True):
        self.system_instructions = system_instructions or ""
        self.strict_mode = strict_mode

    def check_user_input(self, user_input: str) -> GuardResult:
        """
        Check user input for instruction leakage or override attempts.

        Args:
            user_input: The user's prompt text.

        Returns:
            GuardResult with protection status.
        """
        details: List[str] = []
        leak_detected = False
        override_detected = False
        risk_score = 0.0

        # Check for instruction leak attempts
        for pattern in self.LEAK_PATTERNS:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                leak_detected = True
                risk_score += 0.3
                details.append(f"Leak pattern detected: '{match.group(0)[:50]}'")

        # Check for override attempts
        for pattern in self.OVERRIDE_PATTERNS:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                override_detected = True
                risk_score += 0.25
                details.append(f"Override pattern detected: '{match.group(0)[:50]}'")

        # Check for system instruction boundary violations
        boundary_signals = [
            (r"\[\s*(?:system|user)\s*\]", 0.15),
            (r"(?:system|user)\s*:", 0.1),
            (r"<\|im_start\|>", 0.2),
        ]
        for pattern, weight in boundary_signals:
            if re.search(pattern, user_input, re.IGNORECASE):
                risk_score += weight
                details.append(f"Boundary signal detected: '{pattern}'")

        risk_score = min(1.0, risk_score)
        protected = not (leak_detected or override_detected) or risk_score < 0.5

        return GuardResult(
            protected=protected,
            instruction_leak_detected=leak_detected,
            instruction_override_detected=override_detected,
            risk_score=risk_score,
            details=details,
        )

    def validate_prompt(self, prompt: str, role: str = "user") -> GuardResult:
        """
        Validate that a prompt respects instruction hierarchy.

        Args:
            prompt: The full prompt to validate.
            role: The role submitting the prompt.

        Returns:
            GuardResult.
        """
        # For "user" role, check for leaks and overrides
        if role == "user":
            return self.check_user_input(prompt)

        # For "system" or "agent" roles, be less strict
        return GuardResult(protected=True)
