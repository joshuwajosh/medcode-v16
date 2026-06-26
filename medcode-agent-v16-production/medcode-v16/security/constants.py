"""
MedCode AI — Shared Security Constants
=====================================
Single source of truth for Role enum and PERMISSIONS dict.
Previously duplicated between security/auth.py and security/access_control.py.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set


# API Key Configuration
API_KEY_HEADER = "X-API-Key"
API_KEY_PREFIX = "mk_"


class Role(str, Enum):
    ADMIN = "admin"
    MEDICAL_CODER = "medical_coder"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"
    PROVIDER = "provider"
    READ_ONLY = "read_only"


PERMISSIONS: Dict[str, Set[Role]] = {
    "submit_note": {Role.ADMIN, Role.PROVIDER, Role.MEDICAL_CODER},
    "view_codes": {Role.ADMIN, Role.MEDICAL_CODER, Role.REVIEWER, Role.PROVIDER},
    "edit_codes": {Role.ADMIN, Role.MEDICAL_CODER},
    "approve_review": {Role.ADMIN, Role.REVIEWER},
    "reject_review": {Role.ADMIN, Role.REVIEWER},
    "view_audit_log": {Role.ADMIN, Role.AUDITOR, Role.REVIEWER},
    "export_codes": {Role.ADMIN, Role.MEDICAL_CODER},
    "view_phi": {Role.ADMIN, Role.PROVIDER},
    "manage_users": {Role.ADMIN},
    "view_benchmark": {Role.ADMIN, Role.AUDITOR},
    "run_pipeline": {Role.ADMIN, Role.MEDICAL_CODER, Role.PROVIDER},
    "emergency_access": {Role.ADMIN},
}
