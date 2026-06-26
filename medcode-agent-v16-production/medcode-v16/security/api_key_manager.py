"""
MedCode AI V16 — API Key Manager
================================
Handles API key authentication for third-party integrations.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from security.constants import API_KEY_HEADER, API_KEY_PREFIX


class APIKeyPermission(str, Enum):
    """API key permission levels."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    BILLING = "billing"
    CODING = "coding"
    COMPLIANCE = "compliance"


class APIKeyStatus(str, Enum):
    """API key status."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKeyManager:
    """
    Manages API keys for third-party integrations.
    
    Features:
    - Secure key generation with prefix
    - Permission-based access control
    - Rate limiting per key
    - Expiration support
    - Audit logging
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the API key manager.
        
        Args:
            storage_path: Path to store API keys (None uses in-memory)
        """
        self.storage_path = storage_path
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._load_keys()
    
    def _load_keys(self) -> None:
        """Load API keys from storage."""
        if self.storage_path:
            try:
                import json
                import os
                if os.path.exists(self.storage_path):
                    with open(self.storage_path, 'r') as f:
                        self._keys = json.load(f)
            except Exception:
                self._keys = {}
    
    def _save_keys(self) -> None:
        """Save API keys to storage."""
        if self.storage_path:
            try:
                import json
                import os
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, 'w') as f:
                    json.dump(self._keys, f, indent=2)
            except Exception as e:
                raise RuntimeError(f"Failed to save API keys: {e}")
    
    def _hash_key(self, key: str) -> str:
        """
        Hash an API key for storage.
        
        Args:
            key: The API key to hash
            
        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_key(
        self,
        name: str,
        permissions: List[APIKeyPermission],
        expires_in_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new API key.
        
        Args:
            name: Human-readable name for the key
            permissions: List of permissions for this key
            expires_in_days: Number of days until expiration (None = never)
            rate_limit: Maximum requests per minute (None = default)
            metadata: Additional metadata to store
            
        Returns:
            Dictionary containing the key details
        """
        # Generate unique key with prefix
        key_id = str(uuid.uuid4())
        raw_key = secrets.token_urlsafe(32)
        api_key = f"{API_KEY_PREFIX}{raw_key}"
        
        # Hash the key for storage (never store raw keys)
        key_hash = self._hash_key(api_key)
        
        # Calculate expiration
        created_at = datetime.utcnow()
        expires_at = None
        if expires_in_days:
            expires_at = created_at + timedelta(days=expires_in_days)
        
        # Create key record
        key_record = {
            "id": key_id,
            "name": name,
            "key_hash": key_hash,
            "permissions": [p.value for p in permissions],
            "status": APIKeyStatus.ACTIVE.value,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "last_used_at": None,
            "usage_count": 0,
            "rate_limit": rate_limit,
            "metadata": metadata or {}
        }
        
        # Store the key
        self._keys[key_id] = key_record
        self._save_keys()
        
        # Return the key (only time the raw key is shown)
        return {
            "id": key_id,
            "key": api_key,
            "name": name,
            "permissions": [p.value for p in permissions],
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    
    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Key record if valid, None otherwise
        """
        if not api_key or not api_key.startswith(API_KEY_PREFIX):
            return None
        
        # Hash the key
        key_hash = self._hash_key(api_key)
        
        # Find matching key
        for key_id, key_record in self._keys.items():
            if key_record["key_hash"] == key_hash:
                # Check status
                if key_record["status"] != APIKeyStatus.ACTIVE.value:
                    return None
                
                # Check expiration
                if key_record["expires_at"]:
                    expires_at = datetime.fromisoformat(key_record["expires_at"])
                    if datetime.utcnow() > expires_at:
                        key_record["status"] = APIKeyStatus.EXPIRED.value
                        self._save_keys()
                        return None
                
                # Update usage stats
                key_record["last_used_at"] = datetime.utcnow().isoformat()
                key_record["usage_count"] = key_record.get("usage_count", 0) + 1
                self._save_keys()
                
                return key_record
        
        return None
    
    def has_permission(self, api_key: str, permission: APIKeyPermission) -> bool:
        """
        Check if an API key has a specific permission.
        
        Args:
            api_key: The API key to check
            permission: The permission to check for
            
        Returns:
            True if the key has the permission, False otherwise
        """
        key_record = self.validate_key(api_key)
        if not key_record:
            return False
        
        # Admin permission grants all permissions
        if APIKeyPermission.ADMIN.value in key_record["permissions"]:
            return True
        
        return permission.value in key_record["permissions"]
    
    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: The ID of the key to revoke
            
        Returns:
            True if the key was revoked, False if not found
        """
        if key_id in self._keys:
            self._keys[key_id]["status"] = APIKeyStatus.REVOKED.value
            self._save_keys()
            return True
        return False
    
    def delete_key(self, key_id: str) -> bool:
        """
        Delete an API key permanently.
        
        Args:
            key_id: The ID of the key to delete
            
        Returns:
            True if the key was deleted, False if not found
        """
        if key_id in self._keys:
            del self._keys[key_id]
            self._save_keys()
            return True
        return False
    
    def list_keys(self, include_revoked: bool = False) -> List[Dict[str, Any]]:
        """
        List all API keys.
        
        Args:
            include_revoked: Whether to include revoked keys
            
        Returns:
            List of key records (without key hashes)
        """
        keys = []
        for key_record in self._keys.values():
            if not include_revoked and key_record["status"] == APIKeyStatus.REVOKED.value:
                continue
            
            # Don't include the key hash in the response
            safe_record = {k: v for k, v in key_record.items() if k != "key_hash"}
            keys.append(safe_record)
        
        return keys
    
    def get_key_by_id(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a key by its ID.
        
        Args:
            key_id: The ID of the key to retrieve
            
        Returns:
            Key record if found, None otherwise
        """
        if key_id in self._keys:
            # Don't include the key hash in the response
            safe_record = {k: v for k, v in self._keys[key_id].items() if k != "key_hash"}
            return safe_record
        return None
    
    def rotate_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Rotate an API key (generate a new key for the same record).
        
        Args:
            key_id: The ID of the key to rotate
            
        Returns:
            New key details if successful, None otherwise
        """
        if key_id not in self._keys:
            return None
        
        old_record = self._keys[key_id]
        
        # Generate new key
        raw_key = secrets.token_urlsafe(32)
        api_key = f"{API_KEY_PREFIX}{raw_key}"
        key_hash = self._hash_key(api_key)
        
        # Update the record
        old_record["key_hash"] = key_hash
        old_record["created_at"] = datetime.utcnow().isoformat()
        old_record["last_used_at"] = None
        old_record["usage_count"] = 0
        
        self._save_keys()
        
        return {
            "id": key_id,
            "key": api_key,
            "name": old_record["name"],
            "permissions": old_record["permissions"],
            "expires_at": old_record["expires_at"]
        }
    
    def get_rate_limit(self, api_key: str) -> Optional[int]:
        """
        Get the rate limit for an API key.
        
        Args:
            api_key: The API key
            
        Returns:
            Rate limit (requests per minute) or None for default
        """
        key_record = self.validate_key(api_key)
        if key_record:
            return key_record.get("rate_limit")
        return None


# Singleton instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """
    Get the singleton API key manager instance.
    
    Returns:
        APIKeyManager instance
    """
    global _api_key_manager
    if _api_key_manager is None:
        import os
        storage_path = os.environ.get("API_KEY_STORAGE_PATH", "data/api_keys.json")
        _api_key_manager = APIKeyManager(storage_path)
    return _api_key_manager


def require_api_key(permission: APIKeyPermission):
    """
    Decorator to require an API key with specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        FastAPI dependency
    """
    from fastapi import Request, HTTPException, Header
    
    async def api_key_dependency(
        x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER)
    ):
        if not x_api_key:
            raise HTTPException(
                status_code=401,
                detail="API key required"
            )
        
        manager = get_api_key_manager()
        if not manager.validate_key(x_api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API key"
            )
        
        if not manager.has_permission(x_api_key, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        
        return x_api_key
    
    return api_key_dependency


def create_api_key_endpoint():
    """
    Create FastAPI endpoints for API key management.
    
    Returns:
        APIRouter with API key endpoints
    """
    from fastapi import APIRouter, HTTPException, Depends
    from pydantic import BaseModel, Field
    from typing import List, Optional
    
    router = APIRouter(prefix="/api/v19/api-keys", tags=["API Keys"])
    
    class CreateAPIKeyRequest(BaseModel):
        name: str = Field(..., description="Human-readable name for the key")
        permissions: List[str] = Field(..., description="List of permissions")
        expires_in_days: Optional[int] = Field(None, description="Expiration in days")
        rate_limit: Optional[int] = Field(None, description="Requests per minute")
    
    class CreateAPIKeyResponse(BaseModel):
        id: str
        key: str
        name: str
        permissions: List[str]
        expires_at: Optional[str]
    
    class APIKeyInfo(BaseModel):
        id: str
        name: str
        permissions: List[str]
        status: str
        created_at: str
        expires_at: Optional[str]
        last_used_at: Optional[str]
        usage_count: int
    
    @router.post("/", response_model=CreateAPIKeyResponse)
    async def create_api_key(request: CreateAPIKeyRequest):
        """Create a new API key."""
        manager = get_api_key_manager()
        
        permissions = [APIKeyPermission(p) for p in request.permissions]
        
        result = manager.generate_key(
            name=request.name,
            permissions=permissions,
            expires_in_days=request.expires_in_days,
            rate_limit=request.rate_limit
        )
        
        return result
    
    @router.get("/", response_model=List[APIKeyInfo])
    async def list_api_keys(include_revoked: bool = False):
        """List all API keys."""
        manager = get_api_key_manager()
        return manager.list_keys(include_revoked=include_revoked)
    
    @router.get("/{key_id}", response_model=APIKeyInfo)
    async def get_api_key(key_id: str):
        """Get an API key by ID."""
        manager = get_api_key_manager()
        key = manager.get_key_by_id(key_id)
        if not key:
            raise HTTPException(status_code=404, detail="API key not found")
        return key
    
    @router.post("/{key_id}/revoke")
    async def revoke_api_key(key_id: str):
        """Revoke an API key."""
        manager = get_api_key_manager()
        if not manager.revoke_key(key_id):
            raise HTTPException(status_code=404, detail="API key not found")
        return {"message": "API key revoked successfully"}
    
    @router.post("/{key_id}/rotate", response_model=CreateAPIKeyResponse)
    async def rotate_api_key(key_id: str):
        """Rotate an API key (generate new key)."""
        manager = get_api_key_manager()
        result = manager.rotate_key(key_id)
        if not result:
            raise HTTPException(status_code=404, detail="API key not found")
        return result
    
    @router.delete("/{key_id}")
    async def delete_api_key(key_id: str):
        """Delete an API key permanently."""
        manager = get_api_key_manager()
        if not manager.delete_key(key_id):
            raise HTTPException(status_code=404, detail="API key not found")
        return {"message": "API key deleted successfully"}
    
    return router
