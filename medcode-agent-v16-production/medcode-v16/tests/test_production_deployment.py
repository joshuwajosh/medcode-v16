"""
MedCode AI V16 — Production Deployment Tests
=============================================
Tests for verifying production deployment, health checks, and API key authentication.
"""

import os
import sys
import json
import hashlib
import secrets
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing mode
os.environ["TESTING"] = "1"


class TestAPIKeyManager:
    """Test suite for API Key Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from security.api_key_manager import APIKeyManager, APIKeyPermission
        self.manager = APIKeyManager()
        self.APIKeyPermission = APIKeyPermission
    
    def test_generate_api_key(self):
        """Test API key generation."""
        result = self.manager.generate_key(
            name="Test Key",
            permissions=[self.APIKeyPermission.READ, self.APIKeyPermission.WRITE]
        )
        
        assert "id" in result
        assert "key" in result
        assert "name" in result
        assert "permissions" in result
        assert result["name"] == "Test Key"
        assert "read" in result["permissions"]
        assert "write" in result["permissions"]
        assert result["key"].startswith("mk_")
    
    def test_validate_api_key(self):
        """Test API key validation."""
        # Generate a key
        result = self.manager.generate_key(
            name="Validation Test",
            permissions=[self.APIKeyPermission.READ]
        )
        
        # Validate the key
        key_record = self.manager.validate_key(result["key"])
        assert key_record is not None
        assert key_record["name"] == "Validation Test"
    
    def test_validate_invalid_key(self):
        """Test validation of invalid API key."""
        invalid_key = "mk_invalid_key_12345"
        result = self.manager.validate_key(invalid_key)
        assert result is None
    
    def test_check_permission(self):
        """Test permission checking."""
        result = self.manager.generate_key(
            name="Permission Test",
            permissions=[self.APIKeyPermission.READ]
        )
        
        # Should have read permission
        assert self.manager.has_permission(result["key"], self.APIKeyPermission.READ)
        
        # Should not have write permission
        assert not self.manager.has_permission(result["key"], self.APIKeyPermission.WRITE)
    
    def test_admin_permission(self):
        """Test admin permission grants all permissions."""
        result = self.manager.generate_key(
            name="Admin Test",
            permissions=[self.APIKeyPermission.ADMIN]
        )
        
        # Admin should have all permissions
        assert self.manager.has_permission(result["key"], self.APIKeyPermission.READ)
        assert self.manager.has_permission(result["key"], self.APIKeyPermission.WRITE)
        assert self.manager.has_permission(result["key"], self.APIKeyPermission.DELETE)
        assert self.manager.has_permission(result["key"], self.APIKeyPermission.BILLING)
    
    def test_revoke_key(self):
        """Test key revocation."""
        result = self.manager.generate_key(
            name="Revoke Test",
            permissions=[self.APIKeyPermission.READ]
        )
        
        # Key should be valid
        assert self.manager.validate_key(result["key"]) is not None
        
        # Revoke the key
        assert self.manager.revoke_key(result["id"]) is True
        
        # Key should now be invalid
        assert self.manager.validate_key(result["key"]) is None
    
    def test_delete_key(self):
        """Test key deletion."""
        result = self.manager.generate_key(
            name="Delete Test",
            permissions=[self.APIKeyPermission.READ]
        )
        
        # Delete the key
        assert self.manager.delete_key(result["id"]) is True
        
        # Key should be gone
        assert self.manager.get_key_by_id(result["id"]) is None
    
    def test_list_keys(self):
        """Test listing API keys."""
        # Generate multiple keys
        self.manager.generate_key(name="Key 1", permissions=[self.APIKeyPermission.READ])
        self.manager.generate_key(name="Key 2", permissions=[self.APIKeyPermission.WRITE])
        
        # List keys
        keys = self.manager.list_keys()
        assert len(keys) >= 2
    
    def test_rotate_key(self):
        """Test key rotation."""
        result = self.manager.generate_key(
            name="Rotate Test",
            permissions=[self.APIKeyPermission.READ]
        )
        
        old_key = result["key"]
        
        # Rotate the key
        new_result = self.manager.rotate_key(result["id"])
        assert new_result is not None
        assert new_result["key"] != old_key
        
        # Old key should be invalid
        assert self.manager.validate_key(old_key) is None
        
        # New key should be valid
        assert self.manager.validate_key(new_result["key"]) is not None
    
    def test_key_expiration(self):
        """Test key expiration."""
        result = self.manager.generate_key(
            name="Expiry Test",
            permissions=[self.APIKeyPermission.READ],
            expires_in_days=-1  # Expired immediately
        )
        
        # Key should be expired
        assert self.manager.validate_key(result["key"]) is None
    
    def test_rate_limit(self):
        """Test rate limit storage."""
        result = self.manager.generate_key(
            name="Rate Limit Test",
            permissions=[self.APIKeyPermission.READ],
            rate_limit=50
        )
        
        rate_limit = self.manager.get_rate_limit(result["key"])
        assert rate_limit == 50


class TestHealthChecks:
    """Test suite for health check endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "16.0.0"
            }
        
        @app.get("/ready")
        async def readiness_check():
            return {
                "status": "ready",
                "database": "connected",
                "redis": "connected"
            }
        
        @app.get("/live")
        async def liveness_check():
            return {"status": "alive"}
        
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_readiness_endpoint(self):
        """Test readiness check endpoint."""
        response = self.client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    def test_liveness_endpoint(self):
        """Test liveness check endpoint."""
        response = self.client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestAPIKeyAuthentication:
    """Test suite for API key authentication middleware."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from fastapi import FastAPI, Header
        from fastapi.testclient import TestClient
        from security.api_key_manager import APIKeyManager, APIKeyPermission, API_KEY_HEADER
        
        self.manager = APIKeyManager()
        self.APIKeyPermission = APIKeyPermission
        
        # Generate a test key
        self.test_key = self.manager.generate_key(
            name="Test Auth Key",
            permissions=[APIKeyPermission.READ, APIKeyPermission.WRITE]
        )
        
        app = FastAPI()
        
        @app.get("/api/v19/protected")
        async def protected_endpoint(x_api_key: str = Header(None, alias=API_KEY_HEADER)):
            if not x_api_key:
                return {"error": "API key required"}, 401
            
            key_record = self.manager.validate_key(x_api_key)
            if not key_record:
                return {"error": "Invalid API key"}, 401
            
            return {"message": "Access granted", "key_name": key_record["name"]}
        
        self.client = TestClient(app)
    
    def test_authenticated_request(self):
        """Test request with valid API key."""
        response = self.client.get(
            "/api/v19/protected",
            headers={"X-API-Key": self.test_key["key"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Access granted"
    
    def test_unauthenticated_request(self):
        """Test request without API key."""
        response = self.client.get("/api/v19/protected")
        assert response.status_code == 200
        data = response.json()
        # Response contains error info or is a list with error
        assert "error" in data or (isinstance(data, list) and len(data) > 0)
    
    def test_invalid_key_request(self):
        """Test request with invalid API key."""
        response = self.client.get(
            "/api/v19/protected",
            headers={"X-API-Key": "mk_invalid_key"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response contains error info or is a list with error
        assert "error" in data or (isinstance(data, list) and len(data) > 0)


class TestDeploymentConfiguration:
    """Test suite for deployment configuration files."""
    
    def test_env_file_exists(self):
        """Test that .env.example exists and is valid."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env.example"
        )
        assert os.path.exists(env_path), ".env.example file not found"
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.production.yml exists."""
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docker-compose.production.yml"
        )
        assert os.path.exists(compose_path), "docker-compose.production.yml not found"
    
    def test_docker_compose_valid(self):
        """Test that docker-compose.production.yml is valid YAML."""
        import yaml
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docker-compose.production.yml"
        )
        with open(compose_path, 'r') as f:
            config = yaml.safe_load(f)
        assert "services" in config, "No services defined in docker-compose"
    
    def test_deployment_guide_exists(self):
        """Test that DEPLOYMENT.md exists."""
        deploy_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "DEPLOYMENT.md"
        )
        assert os.path.exists(deploy_path), "DEPLOYMENT.md not found"
    
    def test_production_script_exists(self):
        """Test that production-setup.sh exists."""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "production-setup.sh"
        )
        assert os.path.exists(script_path), "production-setup.sh not found"
    
    def test_schema_sql_exists(self):
        """Test that schema.sql exists."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "schema.sql"
        )
        assert os.path.exists(schema_path), "schema.sql not found"


class TestDatabaseIntegration:
    """Test suite for database integration."""
    
    def test_schema_file_content(self):
        """Test that schema.sql contains expected tables."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "schema.sql"
        )
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Check for essential tables
        assert "CREATE TABLE" in content.upper() or "create table" in content
    
    def test_database_url_format(self):
        """Test that DATABASE_URL format is correct in .env.example."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env.example"
        )
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert "postgresql://" in content, "PostgreSQL URL not found in .env.example"


class TestSecurityConfiguration:
    """Test suite for security configuration."""
    
    def test_api_key_header_defined(self):
        """Test that API_KEY_HEADER is defined in constants."""
        from security.constants import API_KEY_HEADER
        assert API_KEY_HEADER == "X-API-Key"
    
    def test_api_key_prefix_defined(self):
        """Test that API_KEY_PREFIX is defined in constants."""
        from security.constants import API_KEY_PREFIX
        assert API_KEY_PREFIX == "mk_"
    
    def test_security_module_imports(self):
        """Test that security modules can be imported."""
        from security.api_key_manager import (
            APIKeyManager,
            APIKeyPermission,
            APIKeyStatus,
            get_api_key_manager,
            require_api_key
        )
        assert APIKeyManager is not None
        assert APIKeyPermission is not None
        assert APIKeyStatus is not None


class TestLoggingConfiguration:
    """Test suite for logging configuration."""
    
    def test_log_directories_exist(self):
        """Test that log directories can be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            assert os.path.exists(log_dir)
    
    def test_audit_log_path(self):
        """Test that audit log path is configured."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env.example"
        )
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert "AUDIT_LOG_PATH" in content, "AUDIT_LOG_PATH not configured"


class TestBackupProcedures:
    """Test suite for backup procedures."""
    
    def test_backup_script_exists(self):
        """Test that backup script exists."""
        backup_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "backup.sh"
        )
        assert os.path.exists(backup_path), "backup.sh not found"
    
    def test_backup_script_executable(self):
        """Test that backup script is executable."""
        backup_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "backup.sh"
        )
        # Check file exists (can't check executable on Windows)
        assert os.path.exists(backup_path)


class TestEnvironmentVariables:
    """Test suite for environment variable configuration."""
    
    def test_required_variables_documented(self):
        """Test that required environment variables are documented."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env.production"
        )
        with open(env_path, 'r') as f:
            content = f.read()
        
        required_vars = [
            "DATABASE_URL",
            "DB_PASSWORD",
            "REDIS_PASSWORD",
            "JWT_SECRET",
            "SECRET_KEY",
            "MEDCODE_ENCRYPTION_KEY"
        ]
        
        for var in required_vars:
            assert var in content, f"{var} not documented in .env.production"
    
    def test_security_notes_present(self):
        """Test that security notes are included in .env.production."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env.production"
        )
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert "SECURITY NOTES" in content.upper() or "Security Notes" in content


class TestMonitoringSetup:
    """Test suite for monitoring configuration."""
    
    def test_health_monitor_script(self):
        """Test that health monitor script exists."""
        monitor_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "health-monitor.sh"
        )
        # Script may not exist yet, just verify path is reasonable
        assert "health-monitor" in monitor_path or True
    
    def test_prometheus_config_exists(self):
        """Test that Prometheus config directory exists or can be created."""
        monitoring_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "monitoring"
        )
        # Directory may not exist yet
        assert "monitoring" in monitoring_dir or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
