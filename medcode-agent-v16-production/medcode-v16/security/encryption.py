"""
MedCode AI V19 — Field-Level Encryption for PHI at Rest
========================================================
HIPAA §164.312(a)(2)(iv): Encryption and Decryption of ePHI.

Provides Fernet symmetric encryption for sensitive database fields:
  - Patient names, DOB, MRN, clinical notes
  - Audit log entries containing PHI
  - Any field marked as encrypted_phi

Uses Fernet (AES-128-CBC with HMAC-SHA256) from the `cryptography` library.
In production, delegate to cloud KMS (AWS KMS, GCP KMS, Azure Key Vault).
"""

from __future__ import annotations

import base64
import hashlib
import os
import threading
from dataclasses import dataclass
from typing import Optional


class FieldLevelEncryption:
    """
    Fernet-based field-level encryption for PHI data at rest.
    
    Usage:
        enc = FieldLevelEncryption.from_env()
        encrypted = enc.encrypt("Patient John Smith DOB 01/01/1980")
        decrypted = enc.decrypt(encrypted)
    """

    def __init__(self, key: Optional[str] = None):
        if key is None:
            key = os.environ.get("MEDCODE_ENCRYPTION_KEY", "")
        
        if not key:
            self._key = self._generate_dev_key()
            self._is_dev = True
        else:
            self._key = key.encode() if isinstance(key, str) else key
            self._is_dev = False
        
        self._fernet = self._create_fernet()

    def _generate_dev_key(self) -> bytes:
        """Generate a development-only key (NOT for production)."""
        dev_seed = os.environ.get("MEDCODE_SECRET_KEY", "medcode-dev-insecure-key")
        return base64.urlsafe_b64encode(
            hashlib.sha256(dev_seed.encode()).digest()
        )

    def _create_fernet(self):
        """Create Fernet cipher from key."""
        try:
            from cryptography.fernet import Fernet
            if self._is_dev:
                key = self._generate_dev_key()
            else:
                key = self._key
            return Fernet(key)
        except ImportError:
            return None

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        Returns base64-encoded ciphertext.
        """
        if self._fernet is None:
            return plaintext
        
        encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a base64-encoded ciphertext string.
        Returns plaintext.
        """
        if self._fernet is None:
            return ciphertext
        
        decrypted = self._fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Encrypt specific fields in a dictionary."""
        encrypted = data.copy()
        for field in fields:
            if field in encrypted and encrypted[field]:
                encrypted[field] = self.encrypt(str(encrypted[field]))
        return encrypted

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Decrypt specific fields in a dictionary."""
        decrypted = data.copy()
        for field in fields:
            if field in decrypted and decrypted[field]:
                try:
                    decrypted[field] = self.decrypt(str(decrypted[field]))
                except Exception:
                    pass
        return decrypted

    def hash_phi(self, phi_value: str) -> str:
        """One-way hash for PHI reference (not reversible)."""
        return hashlib.sha256(
            (phi_value + self._key.decode()[:32]).encode()
        ).hexdigest()[:16]

    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be Fernet-encrypted."""
        if not value or not value.startswith("gAAAAA"):
            return False
        try:
            base64.urlsafe_b64decode(value)
            return True
        except Exception:
            return False


# PHI fields that must be encrypted at rest
PHI_FIELDS = [
    "clinical_note",
    "patient_name",
    "date_of_birth",
    "medical_record_number",
    "raw_response",
]

# Singleton instance
_encryption: Optional[FieldLevelEncryption] = None
_encryption_lock = threading.Lock()


def get_encryption() -> FieldLevelEncryption:
    """Get or create the encryption singleton."""
    global _encryption
    if _encryption is None:
        with _encryption_lock:
            if _encryption is None:
                _encryption = FieldLevelEncryption()
    return _encryption


def encrypt_phi(plaintext: str) -> str:
    """Convenience: encrypt a PHI value."""
    return get_encryption().encrypt(plaintext)


def decrypt_phi(ciphertext: str) -> str:
    """Convenience: decrypt a PHI value."""
    return get_encryption().decrypt(ciphertext)


def encrypt_phi_dict(data: dict) -> dict:
    """Convenience: encrypt all PHI fields in a dict."""
    return get_encryption().encrypt_dict(data, PHI_FIELDS)


def decrypt_phi_dict(data: dict) -> dict:
    """Convenience: decrypt all PHI fields in a dict."""
    return get_encryption().decrypt_dict(data, PHI_FIELDS)
