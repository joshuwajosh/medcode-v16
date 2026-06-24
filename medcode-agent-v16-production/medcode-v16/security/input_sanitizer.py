"""
MedCode AI — Input Sanitization Engine
=======================================
Detects SQL injection, XSS, enforces length limits, and applies
character whitelists per field type. Tracks suspicious input rate.
"""

from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger("medcode.security.sanitizer")


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    clean_text: str = ""
    is_suspicious: bool = False
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False
    patterns_detected: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "clean_length": len(self.clean_text),
            "is_suspicious": self.is_suspicious,
            "blocked": self.blocked,
            "warnings": self.warnings,
            "patterns_detected": self.patterns_detected,
        }


# ── SQL Injection Patterns ──────────────────────────────────────────────
_SQL_INJECTION_PATTERNS: List[Tuple[str, str, str]] = [
    (r"(?i:\bUNION\b\s+(?:ALL\s+)?SELECT\b)", "CRITICAL", "UNION SELECT"),
    (r"(?i:\bSELECT\b.*\bFROM\b.*\bWHERE\b)", "CRITICAL", "SELECT FROM WHERE"),
    (r"(?i:\bDROP\s+(?:TABLE|DATABASE|INDEX|VIEW)\b)", "CRITICAL", "DROP statement"),
    (r"(?i:\bINSERT\b\s+INTO\b)", "CRITICAL", "INSERT INTO"),
    (r"(?i:\bUPDATE\b.*\bSET\b)", "HIGH", "UPDATE SET"),
    (r"(?i:\bDELETE\b\s+FROM\b)", "CRITICAL", "DELETE FROM"),
    (r"(?i:\bALTER\b\s+(?:TABLE|DATABASE)\b)", "HIGH", "ALTER statement"),
    (r"(?i:\bEXEC(?:UTE)?\s*\()", "CRITICAL", "EXEC statement"),
    (r"(?i:\bEXEC\s+sp_\w+)", "CRITICAL", "EXEC stored procedure"),
    (r"(?i:\bTRUNCATE\b\s+TABLE\b)", "CRITICAL", "TRUNCATE TABLE"),
    (r"(?i:\bDECLARE\b.*\bCURSOR\b)", "MEDIUM", "DECLARE CURSOR"),
    (r"(?i:\bDECLARE\b.*\bVARCHAR\b)", "MEDIUM", "DECLARE variable"),
    (r"(?i:\bBULK\s+INSERT\b)", "HIGH", "BULK INSERT"),
    (r"(?i:\bSHUTDOWN\b)", "CRITICAL", "SHUTDOWN command"),
    (r"(?i:\bLOAD_FILE\b\s*\()", "CRITICAL", "LOAD_FILE function"),
    (r"(?i:\bINTO\s+(?:OUTFILE|DUMPFILE)\b)", "CRITICAL", "INTO OUTFILE/DUMPFILE"),
    (r"(?i:\bCHAR\s*\(\s*\d+\s*\))", "MEDIUM", "CHAR() function"),
    (r"(?i:\bCONCAT\s*\()", "LOW", "CONCAT function"),
    (r"--\s*$", "HIGH", "SQL comment"),
    (r"(?i:\bOR\b\s+\d+\s*=\s*\d+)", "CRITICAL", "OR 1=1"),
    (r"(?i:\bAND\b\s+\d+\s*=\s*\d+)", "HIGH", "AND 1=1"),
    (r"(?i:\"\s*;\s*--)", "CRITICAL", "Quote semicolon comment"),
    (r"(?i:\"\s*;\s*DROP)", "CRITICAL", "Quote semicolon DROP"),
    (r"(?i:;.*\bSELECT\b)", "HIGH", "Semicolon SELECT"),
    (r"(?i:'.*\bOR\b\s*'.*=\s*')", "CRITICAL", "OR injection in quotes"),
]

# ── XSS Patterns ────────────────────────────────────────────────────────
_XSS_PATTERNS: List[Tuple[str, str, str]] = [
    (r"<script[\s>]", "CRITICAL", "script tag"),
    (r"<script\b", "CRITICAL", "script tag open"),
    (r"javascript\s*:", "CRITICAL", "javascript: URL"),
    (r"(?i:on(?:click|mouseover|load|error|submit|change|focus|blur|keydown|keyup|input)\s*=)", "CRITICAL", "event handler"),
    (r"<img[^>]+onerror\s*=", "CRITICAL", "img onerror"),
    (r"<iframe[\s>]", "HIGH", "iframe tag"),
    (r"<object[\s>]", "HIGH", "object tag"),
    (r"<embed[\s>]", "HIGH", "embed tag"),
    (r"<svg[^>]+onload\s*=", "CRITICAL", "svg onload"),
    (r"<body[^>]+onload\s*=", "CRITICAL", "body onload"),
    (r"<(?:link|meta|base)[^>]*\bhttp-equiv\s*=\s*\"refresh\"", "MEDIUM", "meta refresh"),
    (r"eval\s*\(\s*['\"]", "HIGH", "eval()"),
    (r"document\.(?:cookie|domain|write)", "HIGH", "document access"),
    (r"window\.(?:location|open)", "MEDIUM", "window access"),
    (r"(?:alert|prompt|confirm)\s*\(\s*\)", "HIGH", "alert/prompt/confirm"),
]

# ── Character Whitelists per Field Type ─────────────────────────────────
_FIELD_CONFIGS: Dict[str, Dict] = {
    "general": {
        "max_length": 10000,
        "pattern": re.compile(
            r"^[a-zA-Z0-9\s\.\,\;\:\!\?\-\(\)\/\'\"\@\#\$\%\&\*\+\=\<\>\[\]\{\}\\_\~\`\|^\u00B0\u00B1\u00D7\u00F7\u00B2\u00B3\u00B9\u2070-\u209F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u2B50-\u2B55\u3000-\u303F\uFF00-\uFFEF]+$"
        ),
        "description": "general alphanumeric with punctuation",
    },
    "medical_note": {
        "max_length": 50000,
        "pattern": re.compile(
            r"^[\w\s\.\,\;\:\!\?\-\(\)\/\'\"\@\#\$\%\&\*\+\=\<\>\[\]\{\}\\_\~\`\|\u00B0\u00B1\u00D7\u00F7\u00B2\u00B3\u00B9\u2070-\u209F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u2B50-\u2B55\u3000-\u303F\uFF00-\uFFEF\u2010-\u2027\u2030-\u205E]+$"
        ),
        "description": "medical text with extended Unicode",
    },
    "code": {
        "max_length": 50,
        "pattern": re.compile(r"^[a-zA-Z0-9\.\-]+$"),
        "description": "CPT/ICD codes (alphanumeric, dot, dash)",
    },
    "name": {
        "max_length": 200,
        "pattern": re.compile(r"^[a-zA-Z\s\-\.\'\u00C0-\u024F]+$"),
        "description": "person name (letters, spaces, accents)",
    },
    "id": {
        "max_length": 100,
        "pattern": re.compile(r"^[a-zA-Z0-9\-_]+$"),
        "description": "identifier (alphanumeric, dash, underscore)",
    },
}

# ── Suspicious Input Rate Tracker ───────────────────────────────────────
class _SuspiciousRateTracker:
    """Tracks suspicious input attempts by client IP with sliding window."""

    def __init__(self, window_seconds: int = 300, max_attempts: int = 10):
        self._window = window_seconds
        self._max_attempts = max_attempts
        self._attempts: Dict[str, List[float]] = {}

    def record(self, client_ip: str) -> bool:
        """Record a suspicious attempt. Returns True if rate limit exceeded."""
        now = time.time()
        cutoff = now - self._window
        if client_ip not in self._attempts:
            self._attempts[client_ip] = []
        self._attempts[client_ip] = [
            t for t in self._attempts[client_ip] if t > cutoff
        ]
        self._attempts[client_ip].append(now)
        if len(self._attempts[client_ip]) > self._max_attempts:
            logger.warning(
                "suspicious_rate_limit_exceeded ip=%s attempts=%d",
                client_ip,
                len(self._attempts[client_ip]),
            )
            return True
        return False

    def get_count(self, client_ip: str) -> int:
        now = time.time()
        cutoff = now - self._window
        if client_ip not in self._attempts:
            return 0
        self._attempts[client_ip] = [
            t for t in self._attempts[client_ip] if t > cutoff
        ]
        return len(self._attempts[client_ip])


_rate_tracker = _SuspiciousRateTracker()


def sanitize_input(
    text: str,
    field_type: str = "general",
    client_ip: str = "",
) -> SanitizationResult:
    """
    Sanitize user input text.

    Parameters
    ----------
    text : str
        Raw user input.
    field_type : str
        One of: 'general', 'medical_note', 'code', 'name', 'id'.
    client_ip : str
        Client IP for rate tracking.

    Returns
    -------
    SanitizationResult with clean_text, is_suspicious, warnings, blocked.
    """
    if not text or not isinstance(text, str):
        return SanitizationResult(clean_text=text or "")

    warnings: List[str] = []
    patterns_detected: List[str] = []
    is_suspicious = False
    blocked = False
    clean_text = text

    # 1. SQL injection detection
    for pattern, severity, label in _SQL_INJECTION_PATTERNS:
        if re.search(pattern, text):
            patterns_detected.append(f"SQL:{label}({severity})")
            is_suspicious = True
            if severity == "CRITICAL":
                blocked = True
                warnings.append(f"Critical SQL injection pattern detected: {label}")

    # 2. XSS detection
    for pattern, severity, label in _XSS_PATTERNS:
        if re.search(pattern, text):
            patterns_detected.append(f"XSS:{label}({severity})")
            is_suspicious = True
            if severity == "CRITICAL":
                blocked = True
                warnings.append(f"Critical XSS pattern detected: {label}")

    # 3. Length validation
    config = _FIELD_CONFIGS.get(field_type, _FIELD_CONFIGS["general"])
    max_len = config["max_length"]
    if len(text) > max_len:
        clean_text = text[:max_len]
        warnings.append(f"Input truncated from {len(text)} to {max_len} chars ({field_type})")
        is_suspicious = True

    # 4. Character whitelist (non-blocking, just warning)
    char_pattern = config["pattern"]
    if clean_text and not char_pattern.match(clean_text):
        # Only warn for medical notes, block for others
        if field_type == "medical_note":
            warnings.append(f"Non-standard characters in medical note")
        else:
            warnings.append(f"Non-whitelisted characters in {field_type} field")

    # 5. Rate tracking
    if is_suspicious and client_ip:
        rate_exceeded = _rate_tracker.record(client_ip)
        if rate_exceeded:
            warnings.append("Rate limit exceeded for suspicious inputs")
            # Don't auto-block here — let middleware decide

    if is_suspicious:
        logger.warning(
            "suspicious_input field_type=%s blocked=%s patterns=%s",
            field_type,
            blocked,
            patterns_detected,
        )

    return SanitizationResult(
        clean_text=clean_text,
        is_suspicious=is_suspicious,
        warnings=warnings,
        blocked=blocked,
        patterns_detected=patterns_detected,
    )


def sanitize_dict(
    data: Dict,
    field_types: Optional[Dict[str, str]] = None,
    client_ip: str = "",
) -> Tuple[Dict, bool, List[str]]:
    """
    Sanitize all string values in a dictionary.

    Parameters
    ----------
    data : Dict
        Dictionary with string values to sanitize.
    field_types : Dict[str, str], optional
        Maps field names to field_type. Defaults to 'general'.
    client_ip : str
        Client IP for rate tracking.

    Returns
    -------
    (clean_dict, any_suspicious, all_warnings)
    """
    if not data:
        return data, False, []

    field_types = field_types or {}
    clean = {}
    any_suspicious = False
    all_warnings: List[str] = []

    for key, value in data.items():
        if isinstance(value, str):
            ft = field_types.get(key, "general")
            result = sanitize_input(value, field_type=ft, client_ip=client_ip)
            clean[key] = result.clean_text
            if result.is_suspicious:
                any_suspicious = True
            all_warnings.extend(result.warnings)
        elif isinstance(value, dict):
            c, s, w = sanitize_dict(value, field_types, client_ip)
            clean[key] = c
            if s:
                any_suspicious = True
            all_warnings.extend(w)
        else:
            clean[key] = value

    return clean, any_suspicious, all_warnings
