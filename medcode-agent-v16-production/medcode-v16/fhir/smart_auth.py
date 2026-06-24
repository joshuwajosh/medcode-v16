"""
SMART on FHIR Authorization — handles OAuth2-based SMART v1.0 and v2.0 flows.
"""

import logging
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

SMART_V1_SCOPES = [
    "launch",
    "openid",
    "fhirUser",
    "patient/*.read",
    "user/*.read",
]

SMART_V2_SCOPES = [
    "launch/patient",
    "openid",
    "fhirUser",
    "patient/*.read",
    "user/*.read",
    "offline_access",
]


class SMARTAuth:
    """SMART on FHIR OAuth2 authorization handler."""

    def __init__(
        self,
        authorize_url: str = "",
        token_url: str = "",
        client_id: str = "",
        redirect_uri: str = "",
        scope: str = "launch patient/*.read user/*.read",
        fhir_version: str = "4.0.1",
    ):
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.fhir_version = fhir_version
        self._state_store: dict[str, dict] = {}

    def get_launch_context(self, request: dict) -> dict:
        """Extract SMART launch context from an EHR launch request."""
        iss = request.get("iss", "")
        launch = request.get("launch", "")
        return {
            "iss": iss,
            "launch": launch,
            "scope": self.scope,
            "state": secrets.token_urlsafe(32),
            "aud": iss,
        }

    async def authorize(self, launch_context: dict) -> str:
        """Generate the SMART authorization URL to redirect the user to."""
        state = launch_context.get("state", secrets.token_urlsafe(32))
        self._state_store[state] = {
            "iss": launch_context.get("iss", ""),
            "launch": launch_context.get("launch", ""),
            "created_at": time.time(),
        }
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state,
            "aud": launch_context.get("aud", launch_context.get("iss", "")),
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, state: str) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        if state not in self._state_store:
            raise ValueError(f"Invalid state parameter: {state}")
        launch_info = self._state_store.pop(state)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            token_data = resp.json()
        token_data["launch"] = launch_info.get("launch", "")
        return token_data

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh an existing SMART access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    def validate_scope(self, requested_scope: str, allowed_scopes: Optional[list[str]] = None) -> bool:
        """Validate that requested scopes are within allowed scopes."""
        if allowed_scopes is None:
            allowed_scopes = SMART_V2_SCOPES
        requested = set(requested_scope.split())
        allowed = set()
        for scope in allowed_scopes:
            allowed.add(scope)
            if "*" in scope:
                base = scope.split("/*")[0]
                allowed.add(f"{base}/*.read")
                allowed.add(f"{base}/*.write")
        return requested.issubset(allowed)

    def get_smart_config(self, base_url: str) -> dict:
        """Return SMART on FHIR configuration metadata."""
        return {
            "authorization_endpoint": self.authorize_url,
            "token_endpoint": self.token_url,
            "capabilities": [
                "launch-ehr",
                "launch-standalone",
                "client-public",
                "client-confidential-symmetric",
                "context-ehr-patient",
                "context-standalone-patient",
                "sso-openid-connect",
                "permission-v2",
            ],
            "scopes_supported": SMART_V2_SCOPES,
            "response_types_supported": ["code"],
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
            ],
            "code_challenge_methods_supported": ["S256"],
        }

    def get_well_known_smart(self, base_url: str) -> dict:
        """Return .well-known/smart-configuration endpoint."""
        return {
            "authorization_endpoint": self.authorize_url,
            "token_endpoint": self.token_url,
            "capabilities": [
                "launch-ehr",
                "launch-standalone",
                "client-public",
                "client-confidential-symmetric",
                "context-ehr-patient",
                "sso-openid-connect",
                "permission-v2",
            ],
            "scopes_supported": SMART_V2_SCOPES,
            "response_types_supported": ["code"],
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
            ],
        }
