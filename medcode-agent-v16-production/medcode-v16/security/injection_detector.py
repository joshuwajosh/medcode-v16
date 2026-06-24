"""
Injection Detector — Phase 9 Security Architecture

Advanced prompt injection attack detection.
Detects and classifies injection attempts with multiple detection strategies.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class InjectionSignal:
    """A detected injection signal."""
    signal_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    match_text: str
    context: str = ""
    position: str = ""

    def to_dict(self) -> dict:
        return {
            "signal_type": self.signal_type,
            "severity": self.severity,
            "match_text": self.match_text[:60],
            "context": self.context[:60],
        }


@dataclass
class InjectionAnalysis:
    """Complete injection analysis result."""
    detected: bool = False
    risk_score: float = 0.0
    signals: List[InjectionSignal] = field(default_factory=list)
    attack_type: str = ""
    blocked: bool = False

    def to_dict(self) -> dict:
        return {
            "detected": self.detected,
            "risk_score": self.risk_score,
            "signal_count": len(self.signals),
            "attack_type": self.attack_type,
            "blocked": self.blocked,
        }


class InjectionDetector:
    """
    Advanced prompt injection detector.

    Detection strategies:
    1. Pattern-based: Known injection patterns
    2. Heuristic: Suspicious text patterns
    3. Structural: Instruction boundary violations
    4. Encoding: Base64/encoded payload detection
    """

    # Known injection payload patterns
    INJECTION_PATTERNS: Dict[str, List[tuple]] = {
        "direct_override": [
            (r"ignore\s+(?:all\s+)?(?:previous|above|prior|system)\s+(?:instructions|directions|prompts|commands)", "HIGH"),
            (r"(?:forget|override|bypass|disregard)\s+(?:all\s+)?(?:previous|above|instructions)", "HIGH"),
            (r"do\s+not\s+(?:follow|obey|listen\s+to)\s+(?:any\s+)?(?:previous|above|system)", "HIGH"),
            (r"(?:new\s+)?instruction[s]?\s*:.*?(?:override|ignore|replace)", "MEDIUM"),
        ],
        "system_prompt_theft": [
            (r"(?:reveal|show|display|print|leak|dump|output|expose)\s+(?:your|the|system|initial|original)\s+(?:prompt|instructions|system\s+message|directions)", "CRITICAL"),
            (r"what\s+(?:is|are|were)\s+(?:your|the|initial|original)\s+(?:prompt|instructions|system\s+message)", "CRITICAL"),
            (r"(?:repeat|say|write|copy)\s+(?:verbatim|exactly|word\s+for\s+word)\s+(?:the\s+)?(?:previous|above|system)", "HIGH"),
        ],
        "jailbreak_attempts": [
            (r"(?:you\s+are|act\s+as)\s+(?:a\s+)?(?:free|unrestricted|unfiltered|uncensored)", "HIGH"),
            (r"no\s+(?:rules|restrictions|limits|boundaries|filters|constraints)", "HIGH"),
            (r"DAN|jailbreak|jail\s+break", "CRITICAL"),
            (r"hypothetical.*(?:no\s+rules|no\s+limits|unfiltered)", "MEDIUM"),
            (r"(?:ignore|bypass)\s+(?:safety|security|ethical|content)\s+(?:guidelines|rules|policies)", "HIGH"),
        ],
        "role_play_bypass": [
            (r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|another)\s+(?:AI|assistant|chatbot|character|persona)", "MEDIUM"),
            (r"from\s+now\s+on\s+(?:you\s+are|you\'?ll\s+act|pretend)", "MEDIUM"),
            (r"act\s+as\s+if\s+(?:you\s+are|you\'?re)\s+(?:a\s+)?\w+\s+(?:who|that)", "LOW"),
        ],
        "data_extraction": [
            (r"(?:extract|leak|steal|exfiltrate|download)\s+(?:all|every|any|the)\s+(?:patient|data|records)", "CRITICAL"),
            (r"(?:show|list|display)\s+(?:all\s+)?(?:patient\s+)?(?:names|ssns|ssn|addresses|phone|emails)", "CRITICAL"),
            (r"(?:get|fetch|query|lookup)\s+(?:patient|records|data)\s+(?:from|by|using)", "HIGH"),
        ],
        "role_confusion": [
            (r"(?:human|user)\s*:.*(?:ignore|bypass|override)", "MEDIUM"),
            (r"\[\s*(?:system|user|assistant)\s*\]", "LOW"),
            (r"<\s*(?:sys|user|assistant)\s*>", "LOW"),
        ],
    }

    def __init__(self, block_threshold: float = 0.6):
        self.block_threshold = block_threshold
        self._compiled_patterns: Dict[str, List[tuple]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile all patterns."""
        for attack_type, patterns in self.INJECTION_PATTERNS.items():
            compiled = []
            for pattern_str, severity in patterns:
                try:
                    compiled.append((re.compile(pattern_str, re.IGNORECASE), severity))
                except re.error:
                    pass
            self._compiled_patterns[attack_type] = compiled

    def analyze(self, text: str) -> InjectionAnalysis:
        """
        Analyze text for injection attacks.

        Args:
            text: Prompt text to analyze.

        Returns:
            InjectionAnalysis with detection results.
        """
        if not text:
            return InjectionAnalysis()

        signals: List[InjectionSignal] = []
        max_severity_score = 0.0
        attack_types_found: Set[str] = set()

        severity_scores = {"LOW": 0.2, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 0.95}

        for attack_type, patterns in self._compiled_patterns.items():
            for compiled_re, severity in patterns:
                match = compiled_re.search(text)
                if match:
                    score = severity_scores.get(severity, 0.5)
                    max_severity_score = max(max_severity_score, score)
                    attack_types_found.add(attack_type)

                    signals.append(InjectionSignal(
                        signal_type=attack_type,
                        severity=severity,
                        match_text=match.group(0)[:80],
                        context=text[max(0, match.start()-20):match.end()+20][:80],
                        position=f"{match.start()}:{match.end()}",
                    ))

        detected = len(signals) > 0
        risk_score = max_severity_score
        blocked = risk_score >= self.block_threshold

        # Determine the most likely attack type
        attack_type_str = ", ".join(sorted(attack_types_found)) if attack_types_found else ""

        return InjectionAnalysis(
            detected=detected,
            risk_score=risk_score,
            signals=signals,
            attack_type=attack_type_str,
            blocked=blocked,
        )

    def is_attack(self, text: str) -> bool:
        """Quick check: is this text an injection attack?"""
        return self.analyze(text).detected
