import time

import pytest

from app.providers.resilience import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    run_sync_with_retry,
)


@pytest.mark.anyio
async def test_provider_operation_succeeds_first_attempt():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        return "ok"

    result = await run_sync_with_retry(
        operation,
        provider_name="Test Provider",
        operation_name="test operation",
        timeout_seconds=1,
        max_attempts=3,
        retry_delay_seconds=0,
    )

    assert result == "ok"
    assert calls == 1


@pytest.mark.anyio
async def test_provider_operation_retries_transient_failure():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise RuntimeError(
                "temporary failure"
            )

        return "ok"

    result = await run_sync_with_retry(
        operation,
        provider_name="Test Provider",
        operation_name="test operation",
        timeout_seconds=1,
        max_attempts=3,
        retry_delay_seconds=0,
    )

    assert result == "ok"
    assert calls == 3


@pytest.mark.anyio
async def test_provider_operation_raises_after_retry_exhaustion():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        raise RuntimeError(
            "temporary failure"
        )

    with pytest.raises(
        ProviderUnavailableError,
        match="Test Provider failed",
    ):
        await run_sync_with_retry(
            operation,
            provider_name="Test Provider",
            operation_name="test operation",
            timeout_seconds=1,
            max_attempts=3,
            retry_delay_seconds=0,
        )

    assert calls == 3


@pytest.mark.anyio
async def test_provider_value_error_is_not_retried():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1

        raise ValueError(
            "No data found"
        )

    with pytest.raises(
        ValueError,
        match="No data found",
    ):
        await run_sync_with_retry(
            operation,
            provider_name="Test Provider",
            operation_name="test operation",
            timeout_seconds=1,
            max_attempts=3,
            retry_delay_seconds=0,
        )

    assert calls == 1


@pytest.mark.anyio
async def test_provider_timeout_is_reported():
    def operation():
        time.sleep(
            0.1
        )

        return "late"

    with pytest.raises(
        ProviderTimeoutError,
        match="timed out",
    ):
        await run_sync_with_retry(
            operation,
            provider_name="Test Provider",
            operation_name="slow operation",
            timeout_seconds=0.01,
            max_attempts=1,
            retry_delay_seconds=0,
        )


@pytest.mark.anyio
async def test_provider_retry_configuration_validation():
    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        await run_sync_with_retry(
            lambda: "ok",
            provider_name="Test Provider",
            operation_name="test operation",
            timeout_seconds=1,
            max_attempts=0,
            retry_delay_seconds=0,
        )