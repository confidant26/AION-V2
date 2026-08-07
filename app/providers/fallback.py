from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.providers.resilience import (
    ProviderError,
    ProviderUnavailableError,
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

    for provider in providers:
        provider_name = getattr(
            provider,
            "provider_name",
            provider.__class__.__name__,
        )

        try:
            return await operation(
                provider
            )

        except ValueError as exc:
            last_value_error = exc

            errors.append(
                f"{provider_name}: {exc}"
            )

        except ProviderError as exc:
            provider_error_seen = True

            errors.append(
                f"{provider_name}: {exc}"
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