import pytest

from app.providers.company.fallback import (
    FallbackCompanyProvider,
)
from app.providers.fallback import (
    execute_with_fallback,
)
from app.providers.financial.fallback import (
    FallbackFinancialProvider,
)
from app.providers.market.fallback import (
    FallbackMarketProvider,
)
from app.providers.resilience import (
    ProviderUnavailableError,
)


class FakeCompanyProvider:
    def __init__(
        self,
        *,
        name,
        result=None,
        error=None,
    ):
        self._name = name
        self.result = result
        self.error = error
        self.calls = 0

    @property
    def provider_name(self):
        return self._name

    async def get_company_profile(
        self,
        symbol,
    ):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return self.result


class FakeMarketProvider:
    def __init__(
        self,
        *,
        name,
        result=None,
        error=None,
    ):
        self._name = name
        self.result = result
        self.error = error
        self.calls = 0

    @property
    def provider_name(self):
        return self._name

    async def get_latest_price(
        self,
        symbol,
    ):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return self.result


class FakeFinancialProvider:
    def __init__(
        self,
        *,
        name,
        result=None,
        error=None,
    ):
        self.provider_name = name
        self.result = result
        self.error = error
        self.calls = 0

    async def get_income_statements(
        self,
        symbol,
    ):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return self.result


@pytest.mark.anyio
async def test_company_fallback_uses_second_provider():
    first = FakeCompanyProvider(
        name="Primary",
        error=ValueError(
            "No company data"
        ),
    )

    second = FakeCompanyProvider(
        name="Secondary",
        result={
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
        },
    )

    provider = (
        FallbackCompanyProvider(
            [
                first,
                second,
            ]
        )
    )

    result = (
        await provider
        .get_company_profile(
            "AAPL"
        )
    )

    assert (
        result["symbol"]
        == "AAPL"
    )

    assert first.calls == 1
    assert second.calls == 1


@pytest.mark.anyio
async def test_market_fallback_uses_second_provider():
    first = FakeMarketProvider(
        name="Primary",
        error=ProviderUnavailableError(
            "Primary unavailable"
        ),
    )

    second = FakeMarketProvider(
        name="Secondary",
        result={
            "symbol": "AAPL",
            "close": 200,
        },
    )

    provider = (
        FallbackMarketProvider(
            [
                first,
                second,
            ]
        )
    )

    result = (
        await provider
        .get_latest_price(
            "AAPL"
        )
    )

    assert result["close"] == 200
    assert first.calls == 1
    assert second.calls == 1


@pytest.mark.anyio
async def test_financial_fallback_uses_second_provider():
    first = FakeFinancialProvider(
        name="Primary",
        error=ValueError(
            "No financial data"
        ),
    )

    second = FakeFinancialProvider(
        name="Secondary",
        result=[
            {
                "period_type": "annual",
            }
        ],
    )

    provider = (
        FallbackFinancialProvider(
            [
                first,
                second,
            ]
        )
    )

    result = (
        await provider
        .get_income_statements(
            "AAPL"
        )
    )

    assert len(result) == 1
    assert first.calls == 1
    assert second.calls == 1


@pytest.mark.anyio
async def test_fallback_stops_after_success():
    first = FakeCompanyProvider(
        name="Primary",
        result={
            "symbol": "AAPL",
        },
    )

    second = FakeCompanyProvider(
        name="Secondary",
        result={
            "symbol": "SHOULD_NOT_RUN",
        },
    )

    provider = (
        FallbackCompanyProvider(
            [
                first,
                second,
            ]
        )
    )

    result = (
        await provider
        .get_company_profile(
            "AAPL"
        )
    )

    assert (
        result["symbol"]
        == "AAPL"
    )

    assert first.calls == 1
    assert second.calls == 0


@pytest.mark.anyio
async def test_all_value_errors_preserve_not_found():
    providers = [
        FakeCompanyProvider(
            name="Primary",
            error=ValueError(
                "Primary missing"
            ),
        ),
        FakeCompanyProvider(
            name="Secondary",
            error=ValueError(
                "Secondary missing"
            ),
        ),
    ]

    provider = (
        FallbackCompanyProvider(
            providers
        )
    )

    with pytest.raises(
        ValueError,
        match="Secondary missing",
    ):
        await provider.get_company_profile(
            "AAPL"
        )


@pytest.mark.anyio
async def test_provider_failure_becomes_unavailable():
    first = FakeMarketProvider(
        name="Primary",
        error=ProviderUnavailableError(
            "Primary offline"
        ),
    )

    second = FakeMarketProvider(
        name="Secondary",
        error=ValueError(
            "No price"
        ),
    )

    provider = (
        FallbackMarketProvider(
            [
                first,
                second,
            ]
        )
    )

    with pytest.raises(
        ProviderUnavailableError,
        match="All providers failed",
    ):
        await provider.get_latest_price(
            "AAPL"
        )


@pytest.mark.anyio
async def test_empty_provider_list_fails():
    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        FallbackCompanyProvider(
            []
        )


@pytest.mark.anyio
async def test_generic_fallback_requires_provider():
    with pytest.raises(
        ProviderUnavailableError,
        match="No providers",
    ):
        await execute_with_fallback(
            providers=[],
            operation=lambda provider: None,
            operation_name="test",
        )