import time
import uuid
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("setu.access")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    SETU Production Observability & Security Middleware.
    - Generates and propagates X-Request-ID correlation headers.
    - Emits structured access logs with latency metrics.
    - Enforces defensive HTTP security headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate correlation ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"
        request.state.request_id = request_id

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            log_record = {
                "event": "http_request_error",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "latency_ms": round(elapsed_ms, 2),
                "client_ip": client_ip,
                "error": str(exc)
            }
            logger.error(json.dumps(log_record))
            raise exc from None

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Structured access log entry
        log_record = {
            "event": "http_access",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(elapsed_ms, 2),
            "client_ip": client_ip
        }
        logger.info(json.dumps(log_record))

        # Attach Correlation and Defensive Security Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response
