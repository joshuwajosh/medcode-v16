"""
MedCode AI — FastAPI Request/Response Logger Middleware
=======================================================
Logs every request with method, path, status, duration, and user_id.
Assigns a UUID request_id for distributed tracing.
Excludes health check endpoints from logging.
"""

from __future__ import annotations

import logging
import time
import traceback
import uuid
from typing import Callable, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("medcode.api")

EXCLUDED_PATHS: Set[str] = {"/health", "/ready", "/live", "/v1/health", "/v1/ready", "/v1/live"}


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all HTTP requests with structured data."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        path = request.url.path

        if path in EXCLUDED_PATHS or path.startswith("/static"):
            return await call_next(request)

        start_time = time.time()
        status_code = 500
        error_msg = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            error_msg = str(exc)
            logger.exception(
                "Unhandled exception on %s %s",
                request.method,
                path,
            )
            raise
        finally:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            user_id = getattr(request.state, "user_id", "") or ""

            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "",
                "user_agent": request.headers.get("user-agent", ""),
            }
            if user_id:
                log_data["user_id"] = user_id
            if error_msg:
                log_data["error"] = error_msg
            if status_code >= 500:
                log_data["traceback"] = traceback.format_exc()

            if status_code >= 500:
                logger.error("Request completed", extra=log_data)
            elif status_code >= 400:
                logger.warning("Request completed", extra=log_data)
            else:
                logger.info("Request completed", extra=log_data)

            try:
                response.headers["X-Request-ID"] = request_id
            except Exception:
                pass

        return response
