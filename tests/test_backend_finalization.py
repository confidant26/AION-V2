import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.company.fallback import (
    FallbackCompanyProvider,
)
from app.providers.telemetry import (
    get_provider_trace_summary,
    reset_provider_trace,
)
from app.services.market_data_service import (
    MarketDataService,
)


client = TestClient(app)


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

    @property
    def provider_name(self):
        return self._name

    async def get_company_profile(
        self,
        symbol,
    ):
        if self.error is not None:
            raise self.error

        return self.result


def test_request_id_is_added_to_response():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers.get(
        "X-Request-ID"
    )


def test_request_id_is_preserved():
    response = client.get(
        "/",
        headers={
            "X-Request-ID": "test-request-id",
        },
    )

    assert response.headers[
        "X-Request-ID"
    ] == "test-request-id"


@pytest.mark.anyio
async def test_fallback_telemetry_reports_secondary_provider():
    reset_provider_trace()

    provider = FallbackCompanyProvider(
        [
            FakeCompanyProvider(
                name="Primary",
                error=ValueError(
                    "missing"
                ),
            ),
            FakeCompanyProvider(
                name="Secondary",
                result={
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                },
            ),
        ]
    )

    result = await provider.get_company_profile(
        "AAPL"
    )

    summary = get_provider_trace_summary()

    assert result["symbol"] == "AAPL"
    assert summary["fallback_used"] is True
    assert summary["event_count"] == 2
    assert summary["events"][0][
        "status"
    ] == "data_error"
    assert summary["events"][1][
        "provider"
    ] == "Secondary"


def test_market_data_service_uses_configured_chain_by_default(
    monkeypatch,
):
    captured = []

    class FakeProvider:
        pass

    monkeypatch.setattr(
        "app.services.market_data_service."
        "MarketProviderFactory.create",
        lambda provider_name=None: (
            captured.append(
                provider_name
            )
            or FakeProvider()
        ),
    )

    MarketDataService()

    assert captured == [None]


def test_system_provider_configuration_is_visible():
    response = client.get(
        "/system/providers"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["financial"][0] == "sec"
    assert body["financial"][1] == "yahoo"
    assert "provider_policy" in body
    assert "rate_limit" in body

from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.services.freshness_service import (
    AssetFreshnessService,
)


class _FreshnessAssetRepository:
    def get_by_symbol(
        self,
        symbol,
    ):
        if symbol == "INVALID":
            return None

        return SimpleNamespace(
            id=1,
            symbol=symbol,
        )


class _FreshnessMarketRepository:
    def __init__(
        self,
        timestamp,
    ):
        self.timestamp = timestamp

    def get_latest_by_asset_id(
        self,
        asset_id,
    ):
        if self.timestamp is None:
            return None

        return SimpleNamespace(
            timestamp=self.timestamp,
        )


class _FreshnessStatementRepository:
    def __init__(
        self,
        period_end_date,
    ):
        self.period_end_date = (
            period_end_date
        )

    def get_by_asset_id(
        self,
        asset_id,
        limit=20,
    ):
        if self.period_end_date is None:
            return []

        return [
            SimpleNamespace(
                period_end_date=(
                    self.period_end_date
                ),
                period_type="quarterly",
            )
        ]


def test_asset_freshness_reports_fresh_components():
    now = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    service = object.__new__(
        AssetFreshnessService
    )
    service.asset_repository = (
        _FreshnessAssetRepository()
    )
    service.market_price_repository = (
        _FreshnessMarketRepository(
            now
        )
    )

    recent_period = date(
        2026,
        6,
        30,
    )

    service.income_statement_repository = (
        _FreshnessStatementRepository(
            recent_period
        )
    )
    service.balance_sheet_repository = (
        _FreshnessStatementRepository(
            recent_period
        )
    )
    service.cash_flow_statement_repository = (
        _FreshnessStatementRepository(
            recent_period
        )
    )

    result = service.get_freshness(
        "aapl",
        now=now,
    )

    assert result.symbol == "AAPL"
    assert result.status == "fresh"
    assert result.stale_components == []


def test_asset_freshness_reports_missing_components_as_stale():
    now = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    service = object.__new__(
        AssetFreshnessService
    )
    service.asset_repository = (
        _FreshnessAssetRepository()
    )
    service.market_price_repository = (
        _FreshnessMarketRepository(
            None
        )
    )
    service.income_statement_repository = (
        _FreshnessStatementRepository(
            None
        )
    )
    service.balance_sheet_repository = (
        _FreshnessStatementRepository(
            None
        )
    )
    service.cash_flow_statement_repository = (
        _FreshnessStatementRepository(
            None
        )
    )

    result = service.get_freshness(
        "AAPL",
        now=now,
    )

    assert result.status == "stale"
    assert set(
        result.stale_components
    ) == {
        "market_price",
        "income_statements",
        "balance_sheets",
        "cash_flow_statements",
    }
