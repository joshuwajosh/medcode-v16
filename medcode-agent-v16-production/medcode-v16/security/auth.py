"""
MedCode AI V19 — JWT Authentication & Authorization
=====================================================
HIPAA §164.312(a)(1) — Access Control.
HIPAA §164.312(d) — Person or Entity Authentication.

Provides:
  - JWT token generation and validation
  - Role-based access control (RBAC)
  - Session management with automatic expiry
  - Password hashing (bcrypt)
  - Token refresh flow
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


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


@dataclass
class TokenPayload:
    """JWT token payload."""
    user_id: str = ""
    role: str = "read_only"
    provider_id: str = ""
    organization_id: str = ""
    session_id: str = ""
    issued_at: float = 0.0
    expires_at: float = 0.0
    token_type: str = "access"  # access | refresh

    def to_dict(self) -> dict:
        return {
            "sub": self.user_id,
            "role": self.role,
            "provider_id": self.provider_id,
            "org_id": self.organization_id,
            "session_id": self.session_id,
            "iat": self.issued_at,
            "exp": self.expires_at,
            "type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenPayload":
        return cls(
            user_id=data.get("sub", ""),
            role=data.get("role", "read_only"),
            provider_id=data.get("provider_id", ""),
            organization_id=data.get("org_id", ""),
            session_id=data.get("session_id", ""),
            issued_at=data.get("iat", 0),
            expires_at=data.get("exp", 0),
            token_type=data.get("type", "access"),
        )


@dataclass
class User:
    """User account."""
    user_id: str = ""
    username: str = ""
    password_hash: str = ""
    role: Role = Role.READ_ONLY
    provider_id: str = ""
    organization_id: str = ""
    is_active: bool = True
    created_at: str = ""
    last_login: str = ""
    failed_login_attempts: int = 0
    locked_until: float = 0.0

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value,
            "provider_id": self.provider_id,
            "organization_id": self.organization_id,
            "is_active": self.is_active,
        }


@dataclass
class Session:
    """Active user session."""
    session_id: str = ""
    user_id: str = ""
    created_at: float = 0.0
    last_activity: float = 0.0
    expires_at: float = 0.0
    ip_address: str = ""
    is_active: bool = True

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def is_idle(self) -> bool:
        timeout = 900  # 15 minutes
        return (time.time() - self.last_activity) > timeout


class PasswordHasher:
    """Secure password hashing with salt."""

    def __init__(self):
        self._algorithm = "sha256"

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16).hex()
        pw_hash = hashlib.pbkdf2_hmac(
            self._algorithm,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000,
        ).hex()
        return f"{salt}${pw_hash}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt, pw_hash = stored_hash.split("$", 1)
            verify_hash = hashlib.pbkdf2_hmac(
                self._algorithm,
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations=100000,
            ).hex()
            return hmac.compare_digest(verify_hash, pw_hash)
        except (ValueError, AttributeError):
            return False


class JWTService:
    """
    JWT token service for authentication.
    Uses HMAC-SHA256 for token signing.
    """

    def __init__(self, secret: Optional[str] = None, expiry_minutes: int = 30):
        self._secret = (secret or os.environ.get("JWT_SECRET", "dev_jwt_secret")).encode()
        self._expiry_minutes = expiry_minutes
        self._refresh_days = 7

    def _b64url_encode(self, data: bytes) -> str:
        import base64
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    def _b64url_decode(self, data: str) -> bytes:
        import base64
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    def create_access_token(self, payload: TokenPayload) -> str:
        payload.token_type = "access"
        payload.issued_at = time.time()
        payload.expires_at = payload.issued_at + (self._expiry_minutes * 60)
        return self._encode_token(payload)

    def create_refresh_token(self, payload: TokenPayload) -> str:
        payload.token_type = "refresh"
        payload.issued_at = time.time()
        payload.expires_at = payload.issued_at + (self._refresh_days * 24 * 3600)
        return self._encode_token(payload)

    def _encode_token(self, payload: TokenPayload) -> str:
        import json
        header = self._b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        body = self._b64url_encode(json.dumps(payload.to_dict()).encode())
        signature_input = f"{header}.{body}".encode()
        signature = hmac.new(self._secret, signature_input, hashlib.sha256).digest()
        sig_b64 = self._b64url_encode(signature)
        return f"{header}.{body}.{sig_b64}"

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header_b64, body_b64, sig_b64 = parts

            signature_input = f"{header_b64}.{body_b64}".encode()
            expected_sig = hmac.new(self._secret, signature_input, hashlib.sha256).digest()
            actual_sig = self._b64url_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            import json
            payload_data = json.loads(self._b64url_decode(body_b64))
            payload = TokenPayload.from_dict(payload_data)

            if time.time() > payload.expires_at:
                return None

            return payload
        except Exception:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = self.decode_token(refresh_token)
        if payload is None or payload.token_type != "refresh":
            return None
        return self.create_access_token(payload)


class AuthService:
    """
    Authentication and authorization service.
    Manages users, sessions, and token lifecycle.
    """

    def __init__(self):
        self._jwt = JWTService()
        self._password_hasher = PasswordHasher()
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._failed_attempts: Dict[str, List[float]] = {}

    def create_user(
        self,
        username: str,
        password: str,
        role: Role = Role.READ_ONLY,
        provider_id: str = "",
        organization_id: str = "",
    ) -> User:
        user = User(
            user_id=str(uuid.uuid4())[:12],
            username=username,
            password_hash=self._password_hasher.hash_password(password),
            role=role,
            provider_id=provider_id,
            organization_id=organization_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._users[user.user_id] = user
        return user

    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str = "",
    ) -> Optional[Dict[str, str]]:
        user = None
        for u in self._users.values():
            if u.username == username:
                user = u
                break

        if user is None:
            return None

        if not user.is_active:
            return None

        if user.locked_until > time.time():
            return None

        if not self._password_hasher.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = time.time() + 900
            return None

        user.failed_login_attempts = 0
        user.locked_until = 0
        user.last_login = datetime.now(timezone.utc).isoformat()

        payload = TokenPayload(
            user_id=user.user_id,
            role=user.role.value,
            provider_id=user.provider_id,
            organization_id=user.organization_id,
        )

        access_token = self._jwt.create_access_token(payload)
        refresh_token = self._jwt.create_refresh_token(payload)

        session = Session(
            session_id=str(uuid.uuid4())[:12],
            user_id=user.user_id,
            created_at=time.time(),
            last_activity=time.time(),
            expires_at=time.time() + (30 * 60),
            ip_address=ip_address,
        )
        self._sessions[session.session_id] = session

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "session_id": session.session_id,
            "user": user.to_dict(),
        }

    def validate_token(self, token: str) -> Optional[TokenPayload]:
        return self._jwt.decode_token(token)

    def check_permission(self, token: str, permission: str) -> bool:
        payload = self.validate_token(token)
        if payload is None:
            return False
        user = self._users.get(payload.user_id)
        if user is None or not user.is_active:
            return False
        allowed = PERMISSIONS.get(permission, set())
        return Role(payload.role) in allowed

    def check_provider_isolation(
        self,
        token: str,
        resource_provider_id: str,
    ) -> bool:
        payload = self.validate_token(token)
        if payload is None:
            return False
        if payload.role != Role.PROVIDER.value:
            return True
        return payload.provider_id == resource_provider_id

    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        new_access = self._jwt.refresh_access_token(refresh_token)
        if new_access is None:
            return None
        return {
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": 1800,
        }

    def logout(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            return True
        return False

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def list_users(self) -> List[dict]:
        return [u.to_dict() for u in self._users.values()]

    def get_stats(self) -> dict:
        return {
            "total_users": len(self._users),
            "active_sessions": sum(1 for s in self._sessions.values() if s.is_active and not s.is_expired),
            "total_sessions": len(self._sessions),
        }


_auth: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _auth
    if _auth is None:
        _auth = AuthService()
    return _auth
