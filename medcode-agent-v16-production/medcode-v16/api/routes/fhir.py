"""
FHIR R4 API Routes — mounts all FHIR endpoints under /fhir/.
Returns FHIR-compliant JSON (application/fhir+json) with OperationOutcome error handling.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fhir", tags=["FHIR R4"])


def _fhir_response(data: dict, status_code: int = 200) -> JSONResponse:
    """Return a FHIR JSON response with correct Content-Type."""
    return JSONResponse(
        content=data,
        status_code=status_code,
        media_type="application/fhir+json",
    )


def _operation_outcome(
    severity: str,
    code: str,
    diagnostics: str,
    status_code: int = 400,
) -> JSONResponse:
    """Return a FHIR OperationOutcome error."""
    return _fhir_response(
        {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": severity,
                    "code": code,
                    "diagnostics": diagnostics,
                }
            ],
        },
        status_code=status_code,
    )


def _get_server(request: Request):
    """Get or create FHIRServer singleton on app.state."""
    server = getattr(request.app.state, "fhir_server", None)
    if server is None:
        from fhir.fhir_server import FHIRServer
        server = FHIRServer()
        request.app.state.fhir_server = server
    return server


# ── Patient ────────────────────────────────────────────────────────────


@router.get("/Patient/{patient_id}")
async def get_patient(patient_id: str, request: Request, _format: str = Query("json")):
    server = _get_server(request)
    try:
        resource = server.get_patient(patient_id)
        return _fhir_response(resource)
    except Exception as exc:
        logger.error("GET /fhir/Patient/%s failed: %s", patient_id, exc)
        return _operation_outcome("error", "processing", str(exc), 500)


@router.get("/Patient")
async def search_patients(
    request: Request,
    family: Optional[str] = None,
    given: Optional[str] = None,
    identifier: Optional[str] = None,
    birthdate: Optional[str] = None,
    _format: str = Query("json"),
):
    server = _get_server(request)
    try:
        params = {}
        if family:
            params["family"] = family
        if given:
            params["given"] = given
        if identifier:
            params["identifier"] = identifier
        if birthdate:
            params["birthdate"] = birthdate
        bundle = {
            "resourceType": "Bundle",
            "id": "patient-search",
            "meta": {"lastUpdated": server._now()},
            "type": "searchset",
            "total": 0,
            "entry": [],
        }
        return _fhir_response(bundle)
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


# ── Encounter ──────────────────────────────────────────────────────────


@router.get("/Encounter/{encounter_id}")
async def get_encounter(encounter_id: str, request: Request, _format: str = Query("json")):
    server = _get_server(request)
    try:
        resource = server.get_encounter(encounter_id)
        return _fhir_response(resource)
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


# ── DocumentReference ──────────────────────────────────────────────────


@router.get("/DocumentReference/{doc_id}")
async def get_document_reference(doc_id: str, request: Request, _format: str = Query("json")):
    server = _get_server(request)
    try:
        resource = server.get_document_reference(doc_id)
        return _fhir_response(resource)
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


@router.get("/DocumentReference")
async def search_document_references(
    request: Request,
    patient: Optional[str] = None,
    _format: str = Query("json"),
):
    server = _get_server(request)
    try:
        if patient:
            return _fhir_response(
                server.get_document_references_for_patient(patient)
            )
        return _fhir_response(
            {
                "resourceType": "Bundle",
                "id": "doc-search",
                "meta": {"lastUpdated": server._now()},
                "type": "searchset",
                "total": 0,
                "entry": [],
            }
        )
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


@router.post("/DocumentReference")
async def create_document_reference(request: Request):
    try:
        body = await request.json()
        server = _get_server(request)
        note_text = ""
        for content in body.get("content", []):
            att = content.get("attachment", {})
            import base64
            data = att.get("data", "")
            if data:
                note_text = base64.b64decode(data).decode("utf-8")
                break
        patient_ref = body.get("subject", {})
        patient_id = patient_ref.get("reference", "unknown").replace("Patient/", "")
        resource = server.create_document_reference(note_text, patient_id)
        return _fhir_response(resource, status_code=201)
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 400)


# ── Concept / ValueSet ($expand / $validate-code) ─────────────────────


@router.get("/Concept")
async def concept_expand(
    request: Request,
    system: str = Query(..., description="Code system: cpt or icd10"),
    filter: Optional[str] = Query(None),
    _format: str = Query("json"),
):
    server = _get_server(request)
    try:
        resource = server.get_concept_expand(system, filter)
        return _fhir_response(resource)
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


@router.get("/ValueSet")
async def value_sets_list(request: Request, _format: str = Query("json")):
    server = _get_server(request)
    try:
        from fhir.value_sets import FHIRValueSetManager
        manager = FHIRValueSetManager()
        return _fhir_response(
            {
                "resourceType": "Bundle",
                "id": "valueset-list",
                "meta": {"lastUpdated": server._now()},
                "type": "searchset",
                "total": 2,
                "entry": [
                    {
                        "fullUrl": f"http://medcode.ai/fhir/ValueSet/cpt",
                        "resource": manager.get_value_set_metadata("cpt"),
                    },
                    {
                        "fullUrl": f"http://medcode.ai/fhir/ValueSet/icd-10-cm",
                        "resource": manager.get_value_set_metadata("icd-10"),
                    },
                ],
            }
        )
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


@router.get("/ValueSet/{value_set_id}")
async def get_value_set(
    value_set_id: str,
    request: Request,
    filter: Optional[str] = Query(None),
    _format: str = Query("json"),
):
    server = _get_server(request)
    try:
        resource = server.get_value_set(value_set_id, filter)
        return _fhir_response(resource)
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)


# ── Capability Statement ──────────────────────────────────────────────


@router.get("/metadata")
async def capability_statement(request: Request):
    server = _get_server(request)
    return _fhir_response(
        {
            "resourceType": "CapabilityStatement",
            "id": "medcode-fhir",
            "meta": {"lastUpdated": server._now()},
            "status": "active",
            "date": server._now(),
            "kind": "instance",
            "software": {
                "name": "MedCode AI",
                "version": "19.0.0",
            },
            "fhirVersion": "4.0.1",
            "format": ["json"],
            "rest": [
                {
                    "mode": "server",
                    "security": {
                        "cors": True,
                        "service": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                                        "code": "SMART-on-FHIR",
                                    }
                                ],
                                "text": "SMART on FHIR OAuth2",
                            }
                        ],
                    },
                    "resource": [
                        {
                            "type": "Patient",
                            "interaction": [
                                {"code": "read"},
                                {"code": "search-type"},
                            ],
                        },
                        {
                            "type": "Encounter",
                            "interaction": [
                                {"code": "read"},
                                {"code": "search-type"},
                            ],
                        },
                        {
                            "type": "DocumentReference",
                            "interaction": [
                                {"code": "read"},
                                {"code": "search-type"},
                                {"code": "create"},
                            ],
                        },
                        {
                            "type": "ValueSet",
                            "interaction": [
                                {"code": "read"},
                            ],
                        },
                    ],
                    "interaction": [
                        {"code": "transaction"},
                    ],
                }
            ],
        }
    )


# ── SMART on FHIR well-known endpoints ────────────────────────────────


@router.get("/.well-known/smart-configuration")
async def smart_configuration(request: Request):
    server = _get_server(request)
    try:
        from fhir.smart_auth import SMARTAuth
        auth = SMARTAuth()
        return _fhir_response(auth.get_well_known_smart(""))
    except Exception as exc:
        return _operation_outcome("error", "processing", str(exc), 500)
