"""
MedCode AI — FastAPI Input Sanitization Middleware
===================================================
Intercepts all requests, sanitizes body/params/path, logs suspicious
inputs, and blocks critical SQL injection patterns.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from security.input_sanitizer import sanitize_input, sanitize_dict
from security.audit_logger import log_audit_event

logger = logging.getLogger("medcode.security.middleware")

EXCLUDED_PATHS = frozenset({"/health", "/ready", "/live", "/v1/health", "/v1/ready", "/v1/live"})

# Fields that receive medical text (more permissive whitelist)
MEDICAL_NOTE_FIELDS = frozenset({
    "note_text", "clinical_note", "note", "text", "description",
    "medical_record", "history", "chief_complaint", "hpi",
    "assessment", "plan", "soap_note", "progress_note",
    "operative_note", "discharge_summary", "radiology_report",
})

CODE_FIELDS = frozenset({"cpt_code", "icd_code", "code", "modifier"})
NAME_FIELDS = frozenset({"patient_name", "name", "provider_name", "physician_name"})
ID_FIELDS = frozenset({"patient_id", "note_id", "session_id", "user_id", "id"})


def _get_field_type(key: str) -> str:
    """Determine field type from key name."""
    lower = key.lower()
    if lower in MEDICAL_NOTE_FIELDS:
        return "medical_note"
    if lower in CODE_FIELDS:
        return "code"
    if lower in NAME_FIELDS:
        return "name"
    if lower in ID_FIELDS:
        return "id"
    return "general"


def _extract_body_fields(body: dict) -> dict:
    """Recursively build field_type map from body keys."""
    field_types = {}
    for key in body:
        ft = _get_field_type(key)
        field_types[key] = ft
        if isinstance(body[key], dict):
            for sub_key in body[key]:
                field_types[sub_key] = _get_field_type(sub_key)
    return field_types


class SanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware that sanitizes all incoming request data."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if path in EXCLUDED_PATHS or path.startswith("/static"):
            return await call_next(request)

        client_ip = request.client.host if request.client else ""
        request_id = getattr(request.state, "request_id", "")
        any_suspicious = False
        all_warnings = []

        # ── Sanitize query parameters ──
        try:
            query_params = dict(request.query_params)
            if query_params:
                clean_qp, qp_suspicious, qp_warnings = sanitize_dict(
                    query_params, client_ip=client_ip
                )
                if qp_suspicious:
                    any_suspicious = True
                    all_warnings.extend(qp_warnings)
        except Exception as e:
            logger.warning("query param sanitization error: %s", e)

        # ── Sanitize request body ──
        body_blocked = False
        try:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body_bytes = await request.body()
                if body_bytes:
                    body = json.loads(body_bytes)
                    if isinstance(body, dict):
                        field_types = _extract_body_fields(body)
                        clean_body, body_suspicious, body_warnings = sanitize_dict(
                            body, field_types=field_types, client_ip=client_ip
                        )
                        if body_suspicious:
                            any_suspicious = True
                            all_warnings.extend(body_warnings)
                        # Re-serialize clean body for downstream
                        request._body = json.dumps(clean_body).encode("utf-8")
                    elif isinstance(body, list):
                        for i, item in enumerate(body):
                            if isinstance(item, dict):
                                field_types = _extract_body_fields(item)
                                clean_item, item_susp, item_warn = sanitize_dict(
                                    item, field_types=field_types, client_ip=client_ip
                                )
                                if item_susp:
                                    any_suspicious = True
                                    all_warnings.extend(item_warn)
                                body[i] = clean_item
                        request._body = json.dumps(body).encode("utf-8")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        except Exception as e:
            logger.debug("body sanitization error: %s", e)

        # ── Sanitize path parameters ──
        try:
            for key, value in request.path_params.items():
                if isinstance(value, str):
                    ft = _get_field_type(key)
                    result = sanitize_input(value, field_type=ft, client_ip=client_ip)
                    if result.is_suspicious:
                        any_suspicious = True
                        all_warnings.extend(result.warnings)
                        request.path_params[key] = result.clean_text
        except Exception as e:
            logger.warning("path param sanitization error: %s", e)

        # ── Log suspicious inputs ──
        if any_suspicious:
            log_audit_event(
                action="suspicious_input",
                ip_address=client_ip,
                resource_type="request",
                resource_id=path,
                success=not body_blocked,
                details=f"warnings={all_warnings[:5]}",
                request_id=request_id,
            )
            logger.warning(
                "suspicious_input path=%s ip=%s warnings=%s",
                path, client_ip, all_warnings[:3],
            )

        # ── Block critical SQL injection ──
        for w in all_warnings:
            if "Critical SQL injection" in w:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Request blocked: malicious input detected"},
                )

        # ── Continue to handler ──
        response = await call_next(request)

        # Attach warnings header for non-blocked suspicious requests
        if any_suspicious and response.status_code < 400:
            try:
                response.headers["X-Security-Warnings"] = "; ".join(all_warnings[:3])
            except Exception:
                pass

        return response
