from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any


_provider_events: ContextVar[tuple[dict[str, Any], ...]] = (
    ContextVar(
        "aion_provider_events",
        default=(),
    )
)


def reset_provider_trace() -> None:
    _provider_events.set(())


def record_provider_event(
    *,
    event: str,
    provider: str,
    operation: str,
    status: str,
    attempt: int | None = None,
    provider_index: int | None = None,
    duration_ms: float | None = None,
    error: str | None = None,
) -> None:
    item: dict[str, Any] = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event": event,
        "provider": provider,
        "operation": operation,
        "status": status,
    }

    if attempt is not None:
        item["attempt"] = attempt

    if provider_index is not None:
        item["provider_index"] = provider_index

    if duration_ms is not None:
        item["duration_ms"] = round(
            duration_ms,
            3,
        )

    if error:
        item["error"] = error

    current = _provider_events.get()
    _provider_events.set(
        (*current, item)
    )


def get_provider_trace() -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in _provider_events.get()
    ]


def get_provider_trace_summary() -> dict[str, Any]:
    events = get_provider_trace()

    fallback_used = any(
        event.get("event") == "fallback_provider"
        and event.get("status") == "success"
        and int(
            event.get(
                "provider_index",
                0,
            )
        ) > 0
        for event in events
    )

    successful_providers: list[str] = []

    for event in events:
        if event.get("status") != "success":
            continue

        provider = str(
            event.get(
                "provider",
                "",
            )
        )

        if (
            provider
            and provider not in successful_providers
        ):
            successful_providers.append(provider)

    return {
        "fallback_used": fallback_used,
        "successful_providers": successful_providers,
        "event_count": len(events),
        "events": events,
    }
