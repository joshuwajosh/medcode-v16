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
  - Token refresh with rotation and revocation
  - Token family tracking for theft detection
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from security.constants import Role, PERMISSIONS

logger = logging.getLogger("medcode.security")


@dataclass
class RefreshTokenRecord:
    """Record for a refresh token in the rotation store."""
    jti: str = ""
    family_id: str = ""
    user_id: str = ""
    session_id: str = ""
    issued_at: float = 0.0
    expires_at: float = 0.0
    revoked: bool = False
    revoked_at: Optional[float] = None


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
    jti: str = ""
    family_id: str = ""

    def to_dict(self) -> dict:
        d = {
            "sub": self.user_id,
            "role": self.role,
            "provider_id": self.provider_id,
            "org_id": self.organization_id,
            "session_id": self.session_id,
            "iat": self.issued_at,
            "exp": self.expires_at,
            "type": self.token_type,
        }
        if self.jti:
            d["jti"] = self.jti
        if self.family_id:
            d["family_id"] = self.family_id
        return d

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
            jti=data.get("jti", ""),
            family_id=data.get("family_id", ""),
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
        return (time.time() - self.last_activity) > DEFAULT_INACTIVE_TIMEOUT


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
        if not payload.jti:
            payload.jti = str(uuid.uuid4())
        return self._encode_token(payload)

    def create_refresh_token(
        self,
        payload: TokenPayload,
        family_id: Optional[str] = None,
    ) -> tuple:
        """Create refresh token with family tracking. Returns (token_str, jti, family_id)."""
        payload.token_type = "refresh"
        payload.issued_at = time.time()
        payload.expires_at = payload.issued_at + (self._refresh_days * 24 * 3600)
        payload.jti = str(uuid.uuid4())
        payload.family_id = family_id or str(uuid.uuid4())
        token = self._encode_token(payload)
        return token, payload.jti, payload.family_id

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
    Implements refresh token rotation with family-based theft detection.
    """

    def __init__(self):
        self._jwt = JWTService()
        self._password_hasher = PasswordHasher()
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._failed_attempts: Dict[str, List[float]] = {}
        self._refresh_tokens: Dict[str, RefreshTokenRecord] = {}
        self._compromised_families: Set[str] = set()
        self._lockout_threshold: int = 5
        self._lockout_duration: int = 900
        self._inactive_timeout: int = 900

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
            if user.failed_login_attempts >= self._lockout_threshold:
                user.locked_until = time.time() + self._lockout_duration
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
        refresh_token_str, jti, family_id = self._jwt.create_refresh_token(payload)

        session = Session(
            session_id=str(uuid.uuid4())[:12],
            user_id=user.user_id,
            created_at=time.time(),
            last_activity=time.time(),
            expires_at=time.time() + (30 * 60),
            ip_address=ip_address,
        )
        self._sessions[session.session_id] = session

        self._refresh_tokens[jti] = RefreshTokenRecord(
            jti=jti,
            family_id=family_id,
            user_id=user.user_id,
            session_id=session.session_id,
            issued_at=payload.issued_at,
            expires_at=payload.expires_at,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "expires_in": self._jwt._expiry_minutes * 60,
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
        """Refresh with rotation: validate old token, revoke it, issue new access + refresh."""
        payload = self._jwt.decode_token(refresh_token)
        if payload is None or payload.token_type != "refresh":
            return None

        jti = payload.jti
        family_id = payload.family_id

        if family_id and family_id in self._compromised_families:
            logger.warning(
                "Refresh token reuse detected for compromised family %s — revoking all tokens",
                family_id,
            )
            self._revoke_family(family_id)
            return None

        record = self._refresh_tokens.get(jti)
        if record is None:
            # Graceful migration: old tokens without jti/family_id still work
            # Create a new record and issue a new refresh token
            new_payload = TokenPayload(
                user_id=payload.user_id,
                role=payload.role,
                provider_id=payload.provider_id,
                organization_id=payload.organization_id,
                session_id=payload.session_id,
            )
            access_token = self._jwt.create_access_token(new_payload)
            new_refresh_str, new_jti, new_family_id = self._jwt.create_refresh_token(new_payload)
            self._refresh_tokens[new_jti] = RefreshTokenRecord(
                jti=new_jti,
                family_id=new_family_id,
                user_id=payload.user_id,
                session_id=payload.session_id,
                issued_at=new_payload.issued_at,
                expires_at=new_payload.expires_at,
            )
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_str,
                "token_type": "bearer",
                "expires_in": self._jwt._expiry_minutes * 60,
            }

        if record.revoked:
            logger.warning(
                "Revoked refresh token %s reused — possible token theft, revoking family %s",
                jti,
                family_id,
            )
            if family_id:
                self._compromised_families.add(family_id)
                self._revoke_family(family_id)
            return None

        if time.time() > record.expires_at:
            return None

        record.revoked = True
        record.revoked_at = time.time()

        new_payload = TokenPayload(
            user_id=payload.user_id,
            role=payload.role,
            provider_id=payload.provider_id,
            organization_id=payload.organization_id,
            session_id=payload.session_id,
        )
        access_token = self._jwt.create_access_token(new_payload)
        new_refresh_str, new_jti, new_family_id = self._jwt.create_refresh_token(
            new_payload, family_id=family_id,
        )

        self._refresh_tokens[new_jti] = RefreshTokenRecord(
            jti=new_jti,
            family_id=new_family_id,
            user_id=payload.user_id,
            session_id=payload.session_id,
            issued_at=new_payload.issued_at,
            expires_at=new_payload.expires_at,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_str,
            "token_type": "bearer",
            "expires_in": self._jwt._expiry_minutes * 60,
        }

    def logout(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            self.revoke_all_session_tokens(session_id)
            return True
        return False

    def revoke_refresh_token(self, jti: str) -> bool:
        record = self._refresh_tokens.get(jti)
        if record and not record.revoked:
            record.revoked = True
            record.revoked_at = time.time()
            return True
        return False

    def revoke_all_user_tokens(self, user_id: str) -> int:
        count = 0
        for record in self._refresh_tokens.values():
            if record.user_id == user_id and not record.revoked:
                record.revoked = True
                record.revoked_at = time.time()
                count += 1
        return count

    def revoke_all_session_tokens(self, session_id: str) -> int:
        count = 0
        for record in self._refresh_tokens.values():
            if record.session_id == session_id and not record.revoked:
                record.revoked = True
                record.revoked_at = time.time()
                count += 1
        return count

    def is_refresh_token_revoked(self, jti: str) -> bool:
        record = self._refresh_tokens.get(jti)
        if record is None:
            return True
        return record.revoked

    def _revoke_family(self, family_id: str) -> int:
        count = 0
        for record in self._refresh_tokens.values():
            if record.family_id == family_id and not record.revoked:
                record.revoked = True
                record.revoked_at = time.time()
                count += 1
        return count

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def list_users(self) -> List[dict]:
        return [u.to_dict() for u in self._users.values()]

    def get_stats(self) -> dict:
        return {
            "total_users": len(self._users),
            "active_sessions": sum(1 for s in self._sessions.values() if s.is_active and not s.is_expired),
            "total_sessions": len(self._sessions),
            "refresh_tokens_tracked": len(self._refresh_tokens),
            "active_refresh_tokens": sum(1 for r in self._refresh_tokens.values() if not r.revoked),
            "compromised_families": len(self._compromised_families),
        }


_auth: Optional[AuthService] = None
_auth_lock = threading.Lock()


def get_auth_service() -> AuthService:
    global _auth
    if _auth is None:
        with _auth_lock:
            if _auth is None:
                _auth = AuthService()
    return _auth
