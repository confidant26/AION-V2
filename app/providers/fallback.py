from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import TypeVar

from app.providers.resilience import (
    ProviderError,
    ProviderUnavailableError,
)
from app.providers.telemetry import (
    record_provider_event,
)


T = TypeVar("T")


async def execute_with_fallback(
    *,
    providers: list,
    operation: Callable[
        [object],
        Awaitable[T],
    ],
    operation_name: str,
) -> T:
    if not providers:
        raise ProviderUnavailableError(
            "No providers are configured."
        )

    errors: list[str] = []
    last_value_error: ValueError | None = None
    provider_error_seen = False

    for provider_index, provider in enumerate(
        providers
    ):
        provider_name = getattr(
            provider,
            "provider_name",
            provider.__class__.__name__,
        )
        started_at = perf_counter()

        try:
            result = await operation(
                provider
            )

            record_provider_event(
                event="fallback_provider",
                provider=str(provider_name),
                operation=operation_name,
                status="success",
                provider_index=provider_index,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
            )

            return result

        except ValueError as exc:
            last_value_error = exc

            errors.append(
                f"{provider_name}: {exc}"
            )

            record_provider_event(
                event="fallback_provider",
                provider=str(provider_name),
                operation=operation_name,
                status="data_error",
                provider_index=provider_index,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
                error=str(exc),
            )

        except ProviderError as exc:
            provider_error_seen = True

            errors.append(
                f"{provider_name}: {exc}"
            )

            record_provider_event(
                event="fallback_provider",
                provider=str(provider_name),
                operation=operation_name,
                status="provider_error",
                provider_index=provider_index,
                duration_ms=(
                    perf_counter()
                    - started_at
                ) * 1000,
                error=str(exc),
            )

    if (
        last_value_error is not None
        and not provider_error_seen
    ):
        raise last_value_error

    detail = "; ".join(
        errors
    )

    raise ProviderUnavailableError(
        f"All providers failed while executing "
        f"{operation_name}. "
        f"{detail}"
    )
