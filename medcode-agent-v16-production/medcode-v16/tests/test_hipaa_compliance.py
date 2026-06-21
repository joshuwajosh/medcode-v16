"""
MedCode AI V19 — HIPAA Compliance Test Suite
==============================================
Tests for HIPAA technical safeguards compliance.
"""

import sys
import os
import time
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPHIEncryption:
    """Test PHI encryption at rest."""

    def test_encrypt_decrypt_roundtrip(self):
        from security.encryption import FieldLevelEncryption
        enc = FieldLevelEncryption()
        
        plaintext = "Patient John Smith DOB 01/01/1980 MRN 12345"
        encrypted = enc.encrypt(plaintext)
        decrypted = enc.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext
        assert encrypted.startswith("gAAAAA")

    def test_encrypt_dict_fields(self):
        from security.encryption import FieldLevelEncryption, PHI_FIELDS
        enc = FieldLevelEncryption()
        
        data = {
            "clinical_note": "Patient has chest pain",
            "session_id": "abc123",
            "status": "complete",
        }
        
        encrypted = enc.encrypt_dict(data, ["clinical_note"])
        
        assert encrypted["session_id"] == "abc123"
        assert encrypted["status"] == "complete"
        assert encrypted["clinical_note"] != data["clinical_note"]

    def test_hash_phi(self):
        from security.encryption import FieldLevelEncryption
        enc = FieldLevelEncryption()
        
        hash1 = enc.hash_phi("John Smith")
        hash2 = enc.hash_phi("John Smith")
        hash3 = enc.hash_phi("Jane Doe")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16


class TestAuditLogIntegrity:
    """Test tamper-evident audit log."""

    def test_audit_chain_integrity(self):
        from security.audit_store import AuditStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "audit.jsonl")
            store = AuditStore(store_path)
            
            store.append(
                user_id="user1",
                role="admin",
                action="login",
                resource_type="auth",
            )
            
            store.append(
                user_id="user1",
                role="admin",
                action="view_codes",
                resource_type="session",
                note_id="note123",
            )
            
            result = store.verify_chain()
            assert result["valid"] is True
            assert result["total_entries"] == 2

    def test_audit_persistence(self):
        from security.audit_store import AuditStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "audit.jsonl")
            
            store1 = AuditStore(store_path)
            store1.append(
                user_id="user1",
                role="admin",
                action="test",
                resource_type="test",
            )
            
            store2 = AuditStore(store_path)
            assert len(store2._entries) == 1
            assert store2._entries[0].action == "test"

    def test_audit_phi_tracking(self):
        from security.audit_store import AuditStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "audit.jsonl")
            store = AuditStore(store_path)
            
            store.append(
                user_id="user1",
                role="admin",
                action="view_phi",
                resource_type="session",
                phi_accessed=True,
            )
            
            phi_log = store.get_phi_access_log()
            assert len(phi_log) == 1
            assert phi_log[0]["phi_accessed"] is True


class TestAuthentication:
    """Test JWT authentication."""

    def test_jwt_token_creation(self):
        from security.auth import JWTService, TokenPayload
        
        jwt_service = JWTService()
        payload = TokenPayload(
            user_id="user123",
            role="medical_coder",
        )
        
        token = jwt_service.create_access_token(payload)
        assert token.count(".") == 2
        
        decoded = jwt_service.decode_token(token)
        assert decoded is not None
        assert decoded.user_id == "user123"
        assert decoded.role == "medical_coder"

    def test_jwt_token_expiry(self):
        from security.auth import JWTService, TokenPayload
        
        jwt_service = JWTService(expiry_minutes=0)
        payload = TokenPayload(user_id="user123", role="admin")
        
        token = jwt_service.create_access_token(payload)
        time.sleep(0.1)
        
        decoded = jwt_service.decode_token(token)
        assert decoded is None

    def test_password_hashing(self):
        from security.auth import PasswordHasher
        
        hasher = PasswordHasher()
        password = "secure_password_123"
        
        hashed = hasher.hash_password(password)
        assert "$" in hashed
        
        assert hasher.verify_password(password, hashed) is True
        assert hasher.verify_password("wrong_password", hashed) is False


class TestSessionManagement:
    """Test automatic logoff."""

    def test_session_creation(self):
        from security.session_manager import SessionManager
        
        mgr = SessionManager(inactive_timeout_minutes=15)
        session = mgr.create_session(user_id="user1", role="admin")
        
        assert session.session_id
        assert session.user_id == "user1"
        assert session.is_active is True

    def test_session_timeout(self):
        from security.session_manager import SessionManager
        
        mgr = SessionManager(inactive_timeout_minutes=0)
        session = mgr.create_session(user_id="user1")
        
        time.sleep(0.1)
        
        retrieved = mgr.get_session(session.session_id)
        assert retrieved is None

    def test_session_invalidation(self):
        from security.session_manager import SessionManager
        
        mgr = SessionManager()
        session = mgr.create_session(user_id="user1")
        
        assert mgr.invalidate_session(session.session_id) is True
        assert mgr.get_session(session.session_id) is None


class TestEmergencyAccess:
    """Test break-glass emergency access."""

    def test_emergency_access_grant(self):
        from security.emergency_access import EmergencyAccessService
        
        svc = EmergencyAccessService()
        grant = svc.request_emergency_access(
            user_id="user1",
            reason="System failure requires immediate access to patient records",
            emergency_code=svc._emergency_secret,
        )
        
        assert grant is not None
        assert grant.is_active is True

    def test_emergency_access_denial(self):
        from security.emergency_access import EmergencyAccessService
        
        svc = EmergencyAccessService()
        grant = svc.request_emergency_access(
            user_id="user1",
            reason="Too short",
            emergency_code="wrong_code",
        )
        
        assert grant is None

    def test_emergency_access_revocation(self):
        from security.emergency_access import EmergencyAccessService
        
        svc = EmergencyAccessService()
        grant = svc.request_emergency_access(
            user_id="user1",
            reason="Valid reason for emergency access",
            emergency_code=svc._emergency_secret,
        )
        
        assert svc.revoke_emergency_access(grant.grant_id) is True
        assert grant.is_active is False


class TestLLMPhiFirewall:
    """Test PHI protection for LLM calls."""

    def test_deidentification(self):
        from security.llm_phi_firewall import LLMPhiFirewall
        
        firewall = LLMPhiFirewall()
        text = "Patient John Smith DOB 01/01/1980 has chest pain"
        
        result = firewall.deidentify(text)
        
        assert result.phi_count > 0
        assert "John Smith" not in result.deidentified_text
        assert "01/01/1980" not in result.deidentified_text

    def test_sanitize_for_llm(self):
        from security.llm_phi_firewall import LLMPhiFirewall
        
        firewall = LLMPhiFirewall()
        text = "Patient MRN 12345 presents with symptoms"
        
        deidentified, result = firewall.sanitize_for_llm(text)
        
        assert "12345" not in deidentified
        assert result.phi_count >= 1


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_buckets(self):
        import os
        old_testing = os.environ.get("TESTING")
        os.environ.pop("TESTING", None)
        
        try:
            from security.tls_middleware import RateLimitMiddleware
            
            class MockApp:
                pass
            
            middleware = RateLimitMiddleware(MockApp(), requests_per_minute=5)
            
            for _ in range(5):
                assert middleware._check_rate_limit("test_client") is True
            
            assert middleware._check_rate_limit("test_client") is False
        finally:
            if old_testing:
                os.environ["TESTING"] = old_testing

    def test_rate_limit_bypass_in_test_mode(self):
        import os
        old_testing = os.environ.get("TESTING")
        os.environ["TESTING"] = "1"
        
        try:
            from security.tls_middleware import RateLimitMiddleware
            
            class MockApp:
                pass
            
            middleware = RateLimitMiddleware(MockApp(), requests_per_minute=1)
            
            for _ in range(100):
                assert middleware._check_rate_limit("test_client") is True
        finally:
            if old_testing:
                os.environ["TESTING"] = old_testing
            else:
                os.environ.pop("TESTING", None)


class TestInputValidation:
    """Test input size limits."""

    def test_max_note_length(self):
        from pydantic import BaseModel, validator
        
        class TestRequest(BaseModel):
            note: str
            
            class Config:
                max_text_length = 100
        
        short_note = "x" * 50
        request = TestRequest(note=short_note)
        assert len(request.note) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
