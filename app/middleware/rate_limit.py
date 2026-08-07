import asyncio
import logging
from datetime import datetime, timezone

from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from app.core.config import settings
from app.core.redis import get_redis_client


logger = logging.getLogger(__name__)


class RateLimitMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request,
        call_next,
    ):
        if (
            not settings.rate_limit_enabled
            or request.url.path
            in settings.get_rate_limit_exempt_paths()
        ):
            return await call_next(
                request
            )

        client_host = (
            request.client.host
            if request.client is not None
            else "unknown"
        )

        current_minute = datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M")

        key = (
            f"aion:rate:{client_host}:"
            f"{current_minute}"
        )

        try:
            count = await asyncio.to_thread(
                self._increment,
                key,
            )
        except Exception as exc:
            logger.warning(
                "Rate limiter unavailable; failing open: %s",
                exc,
            )

            return await call_next(
                request
            )

        if (
            count
            > settings.rate_limit_requests_per_minute
        ):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Rate limit exceeded."
                    )
                },
                headers={
                    "Retry-After": "60",
                },
            )

        response = await call_next(
            request
        )

        response.headers[
            "X-RateLimit-Limit"
        ] = str(
            settings.rate_limit_requests_per_minute
        )
        response.headers[
            "X-RateLimit-Remaining"
        ] = str(
            max(
                0,
                settings.rate_limit_requests_per_minute
                - count,
            )
        )

        return response

    @staticmethod
    def _increment(
        key: str,
    ) -> int:
        redis_client = get_redis_client()
        count = int(
            redis_client.incr(
                key
            )
        )

        if count == 1:
            redis_client.expire(
                key,
                61,
            )

        return count
