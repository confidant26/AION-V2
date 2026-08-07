import asyncio
import logging
from collections.abc import Callable
from time import perf_counter
from typing import TypeVar

from app.core.config import settings
from app.providers.telemetry import (
    record_provider_event,
)


T = TypeVar("T")

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


class ProviderTimeoutError(ProviderError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


async def run_sync_with_retry(
    operation: Callable[[], T],
    *,
    provider_name: str,
    operation_name: str,
    timeout_seconds: float | None = None,
    max_attempts: int | None = None,
    retry_delay_seconds: float | None = None,
) -> T:
    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else settings.provider_timeout_seconds
    )

    attempts = (
        max_attempts
        if max_attempts is not None
        else settings.provider_max_attempts
    )

    retry_delay = (
        retry_delay_seconds
        if retry_delay_seconds is not None
        else settings.provider_retry_delay_seconds
    )

    if timeout <= 0:
        raise ValueError(
            "Provider timeout must be greater than zero."
        )

    if attempts < 1:
        raise ValueError(
            "Provider max attempts must be at least one."
        )

    if retry_delay < 0:
        raise ValueError(
            "Provider retry delay cannot be negative."
        )

    for attempt in range(
        1,
        attempts + 1,
    ):
        started_at = perf_counter()

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    operation
                ),
                timeout=timeout,
            )

            record_provider_event(
                event="provider_attempt",
                provider=provider_name,
                operation=operation_name,
                status="success",
                attempt=attempt,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
            )

            return result

        except ValueError as exc:
            record_provider_event(
                event="provider_attempt",
                provider=provider_name,
                operation=operation_name,
                status="data_error",
                attempt=attempt,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
                error=str(exc),
            )
            raise

        except TimeoutError as exc:
            record_provider_event(
                event="provider_attempt",
                provider=provider_name,
                operation=operation_name,
                status="timeout",
                attempt=attempt,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
                error=str(exc),
            )

            if attempt >= attempts:
                raise ProviderTimeoutError(
                    f"{provider_name} timed out while "
                    f"executing {operation_name} after "
                    f"{attempts} attempt(s)."
                ) from exc

            logger.warning(
                "%s timed out during %s "
                "(attempt %s/%s).",
                provider_name,
                operation_name,
                attempt,
                attempts,
            )

        except ProviderError as exc:
            record_provider_event(
                event="provider_attempt",
                provider=provider_name,
                operation=operation_name,
                status="provider_error",
                attempt=attempt,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
                error=str(exc),
            )
            raise

        except Exception as exc:
            record_provider_event(
                event="provider_attempt",
                provider=provider_name,
                operation=operation_name,
                status="error",
                attempt=attempt,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
                error=str(exc),
            )

            if attempt >= attempts:
                raise ProviderUnavailableError(
                    f"{provider_name} failed while "
                    f"executing {operation_name} after "
                    f"{attempts} attempt(s): {exc}"
                ) from exc

            logger.warning(
                "%s failed during %s "
                "(attempt %s/%s): %s",
                provider_name,
                operation_name,
                attempt,
                attempts,
                exc,
            )

        delay = (
            retry_delay
            * (2 ** (attempt - 1))
        )

        if delay > 0:
            await asyncio.sleep(
                delay
            )

    raise ProviderUnavailableError(
        f"{provider_name} failed while "
        f"executing {operation_name}."
    )
