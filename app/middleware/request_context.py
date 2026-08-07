import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from app.core.config import settings
from app.core.logging import (
    reset_request_id,
    set_request_id,
)
from app.providers.telemetry import (
    reset_provider_trace,
)


logger = logging.getLogger("aion.access")


class RequestContextMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request,
        call_next,
    ):
        request_id = (
            request.headers.get(
                settings.request_id_header
            )
            or str(uuid4())
        )

        token = set_request_id(
            request_id
        )
        reset_provider_trace()
        started_at = perf_counter()

        try:
            response = await call_next(
                request
            )

            response.headers[
                settings.request_id_header
            ] = request_id

            return response

        finally:
            duration_ms = (
                perf_counter()
                - started_at
            ) * 1000

            logger.info(
                "%s %s completed in %.3f ms",
                request.method,
                request.url.path,
                duration_ms,
            )

            reset_request_id(
                token
            )
