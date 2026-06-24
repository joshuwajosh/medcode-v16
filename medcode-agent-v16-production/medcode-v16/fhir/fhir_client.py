"""
FHIR R4 Client — async HTTP client for connecting to external EHR systems.
Uses httpx for async HTTP calls with SMART on FHIR authorization support.
"""

import logging
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class FHIRClient:
    """Async FHIR R4 client for querying EHR systems."""

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            }
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    def set_auth_token(self, token: str) -> None:
        self.auth_token = token

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> dict:
        client = await self._get_client()
        try:
            resp = await client.request(method, path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "FHIR request failed: %s %s -> %s",
                method, path, exc.response.status_code,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("FHIR connection error: %s %s -> %s", method, path, exc)
            raise

    async def get_patient(self, patient_id: str) -> dict:
        return await self._request("GET", f"/Patient/{patient_id}")

    async def get_encounter(self, encounter_id: str) -> dict:
        return await self._request("GET", f"/Encounter/{encounter_id}")

    async def get_document_reference(self, doc_id: str) -> dict:
        return await self._request("GET", f"/DocumentReference/{doc_id}")

    async def search_patients(self, query: dict[str, str]) -> dict:
        return await self._request("GET", "/Patient", params=query)

    async def search_encounters(self, patient_id: str) -> dict:
        return await self._request(
            "/Encounter", params={"patient": patient_id}
        )

    async def search_document_references(self, patient_id: str) -> dict:
        return await self._request(
            "/DocumentReference", params={"patient": patient_id}
        )

    async def paginate_bundle(self, bundle: dict) -> list[dict]:
        """Collect all entries from a paginated FHIR Bundle."""
        entries: list[dict] = []
        current = bundle
        while current:
            entries.extend(current.get("entry", []))
            next_url: Optional[str] = None
            for link in current.get("link", []):
                if link.get("relation") == "next":
                    next_url = link.get("url")
                    break
            if next_url:
                client = await self._get_client()
                resp = await client.get(next_url)
                resp.raise_for_status()
                current = resp.json()
            else:
                break
        return entries

    async def get_capabilities(self) -> dict:
        return await self._request("GET", "/metadata")

    async def create_resource(self, resource_type: str, resource: dict) -> dict:
        return await self._request("POST", f"/{resource_type}", json=resource)

    async def update_resource(
        self, resource_type: str, resource_id: str, resource: dict
    ) -> dict:
        return await self._request(
            "PUT", f"/{resource_type}/{resource_id}", json=resource
        )

    async def delete_resource(self, resource_type: str, resource_id: str) -> dict:
        return await self._request(
            "DELETE", f"/{resource_type}/{resource_id}"
        )

    async def __aenter__(self) -> "FHIRClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
