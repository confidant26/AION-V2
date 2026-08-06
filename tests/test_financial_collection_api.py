from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def statement(
    period_end_date,
    period_type,
):
    return SimpleNamespace(
        period_end_date=period_end_date,
        period_type=period_type,
    )


class FakeIncomeStatementService:
    def __init__(
        self,
        db,
        provider,
    ):
        pass

    async def collect_income_statements(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 6, 30),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeBalanceSheetService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_balance_sheets(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 6, 30),
                "quarterly",
            ),
            statement(
                date(2026, 3, 31),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeCashFlowStatementService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_cash_flow_statements(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 6, 30),
                "quarterly",
            ),
            statement(
                date(2026, 3, 31),
                "quarterly",
            ),
            statement(
                date(2025, 12, 31),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeLaggingCashFlowStatementService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_cash_flow_statements(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 3, 31),
                "quarterly",
            ),
            statement(
                date(2025, 12, 31),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeModelResult:
    def __init__(
        self,
        payload,
    ):
        self.payload = payload

    def model_dump(
        self,
        mode=None,
    ):
        return self.payload


class FakeTTMFinancialsService:
    def __init__(
        self,
        db,
    ):
        pass

    def get_ttm_financials(
        self,
        symbol,
    ):
        return FakeModelResult(
            {
                "symbol": "AAPL",
                "period_end_date": "2026-06-30",
                "total_revenue": "466518000000",
                "net_income": "124930000000",
                "free_cash_flow": "134683000000",
                "confidence": "1",
            }
        )


class FakeTTMValuationMetricsService:
    def __init__(
        self,
        db,
    ):
        pass

    def get_ttm_valuation_metrics(
        self,
        symbol,
    ):
        return FakeModelResult(
            {
                "symbol": "AAPL",
                "period_end_date": "2026-06-30",
                "price_to_earnings": "39.20",
                "price_to_sales": "10.50",
                "price_to_book": "45.00",
                "ev_to_ebitda": "30.00",
                "free_cash_flow_yield": "0.027",
                "earnings_yield": "0.0255",
                "confidence": "1",
            }
        )


class FakeCompositeScoreService:
    def __init__(
        self,
        db,
    ):
        pass

    def get_composite_score(
        self,
        symbol,
    ):
        return FakeModelResult(
            {
                "symbol": "AAPL",
                "as_of_date": "2026-06-30",
                "growth_score": "0.54",
                "quality_score": "0.83",
                "valuation_score": "0.38",
                "composite_score": "0.59",
                "confidence": "1.00",
            }
        )


class FakeIncomeStatementNotFoundService:
    def __init__(
        self,
        db,
        provider,
    ):
        pass

    async def collect_income_statements(
        self,
        symbol,
    ):
        raise ValueError(
            "Asset not found for symbol: INVALID"
        )


def patch_collection_services(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.BalanceSheetService",
        FakeBalanceSheetService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )


def patch_analysis_services(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.TTMFinancialsService",
        FakeTTMFinancialsService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.TTMValuationMetricsService",
        FakeTTMValuationMetricsService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.CompositeScoreService",
        FakeCompositeScoreService,
    )


def test_financial_collection_endpoint_success(
    monkeypatch,
):
    patch_collection_services(
        monkeypatch
    )

    response = client.post(
        "/financials/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"

    assert body["counts"] == {
        "income_statements": 2,
        "balance_sheets": 3,
        "cash_flow_statements": 4,
    }

    assert body["total_count"] == 9

    assert body["quarterly_alignment"] == {
        "ok": True,
        "spread_days": 0,
    }

    assert body["data_quality"] == {
        "status": "healthy",
        "warnings": [],
    }

    assert "analysis" not in body


def test_financial_collection_includes_full_analysis(
    monkeypatch,
):
    patch_collection_services(
        monkeypatch
    )

    patch_analysis_services(
        monkeypatch
    )

    response = client.post(
        "/financials/collect/aapl"
        "?include_analysis=true"
    )

    assert response.status_code == 200

    analysis = response.json()["analysis"]

    assert analysis["status"] == "healthy"
    assert analysis["warnings"] == []

    assert (
        analysis["ttm_financials"]["symbol"]
        == "AAPL"
    )

    assert (
        analysis["ttm_financials"][
            "period_end_date"
        ]
        == "2026-06-30"
    )

    assert (
        analysis["ttm_valuation_metrics"][
            "price_to_earnings"
        ]
        == "39.20"
    )

    assert (
        analysis["ttm_valuation_metrics"][
            "ev_to_ebitda"
        ]
        == "30.00"
    )

    assert (
        analysis["composite_score"][
            "composite_score"
        ]
        == "0.59"
    )


def test_financial_collection_warns_on_misalignment(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.BalanceSheetService",
        FakeBalanceSheetService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.CashFlowStatementService",
        FakeLaggingCashFlowStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "latest_quarterly_periods"
    ] == {
        "income_statements": "2026-06-30",
        "balance_sheets": "2026-06-30",
        "cash_flow_statements": "2026-03-31",
    }

    assert body[
        "quarterly_alignment"
    ] == {
        "ok": False,
        "spread_days": 91,
    }

    assert (
        body["data_quality"]["status"]
        == "warning"
    )


def test_financial_collection_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementNotFoundService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Asset not found for symbol: INVALID"
    )