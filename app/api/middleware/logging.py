from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger("api")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and their duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response: Response = await call_next(request)
            elapsed = time.perf_counter() - start
            status = response.status_code
            # Only log non-success or slow requests to reduce noise
            if status >= 400 or elapsed > 1.0:
                logger.info(
                    "%s %s → %d (%.2fs)",
                    method,
                    path,
                    status,
                    elapsed,
                )
        except Exception as exc:
            elapsed = time.perf_counter() - start
            logger.error(
                "%s %s → ERROR (%.2fs): %s",
                method,
                path,
                elapsed,
                exc,
            )
            raise

        return response


def setup_logging(app: FastAPI) -> None:
    """Attach request logging middleware."""
    app.add_middleware(RequestLogMiddleware)
