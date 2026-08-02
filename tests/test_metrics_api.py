from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.dependencies import get_db
from app.main import app


class FakeDB:
    pass


def override_get_db():
    yield FakeDB()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class FakeFinancialMetricsService:
    def __init__(self, db):
        self.db = db

    def get_financial_metrics(
        self,
        symbol: str,
        period_type: str | None = None,
        limit: int = 20,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            {
                "symbol": clean_symbol,
                "period_end_date": date(2025, 9, 30),
                "period_type": period_type or "annual",
                "currency": "USD",
                "operating_margin": Decimal("0.32"),
                "net_margin": Decimal("0.27"),
                "return_on_assets": Decimal("0.31"),
                "return_on_equity": Decimal("1.52"),
                "current_ratio": Decimal("0.89"),
                "debt_to_equity": Decimal("1.34"),
                "free_cash_flow_margin": Decimal("0.24"),
                "income_statement_id": 1,
                "balance_sheet_id": 1,
                "cash_flow_statement_id": 1,
                "missing_fields": [],
                "confidence": Decimal("1"),
            }
        ][:limit]


class FakeGrowthMetricsService:
    def __init__(self, db):
        self.db = db

    def get_growth_metrics(
        self,
        symbol: str,
        limit: int = 10,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            {
                "symbol": clean_symbol,
                "period_end_date": date(2025, 9, 30),
                "previous_period_end_date": date(
                    2024,
                    9,
                    30,
                ),
                "period_type": "annual",
                "currency": "USD",
                "revenue_growth": Decimal("0.06"),
                "operating_income_growth": Decimal("0.08"),
                "net_income_growth": Decimal("0.19"),
                "free_cash_flow_growth": Decimal("-0.09"),
                "total_assets_growth": Decimal("-0.01"),
                "stockholders_equity_growth": Decimal(
                    "0.29"
                ),
                "current_income_statement_id": 1,
                "previous_income_statement_id": 2,
                "current_balance_sheet_id": 1,
                "previous_balance_sheet_id": 2,
                "current_cash_flow_statement_id": 1,
                "previous_cash_flow_statement_id": 2,
                "missing_fields": [],
                "confidence": Decimal("1"),
            }
        ][:limit]


class FakeValuationMetricsService:
    def __init__(self, db):
        self.db = db

    def get_valuation_metrics(
        self,
        symbol: str,
        limit: int = 20,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            {
                "symbol": clean_symbol,
                "period_end_date": date(2025, 9, 30),
                "period_type": "annual",
                "currency": "USD",
                "market_cap": Decimal("1000"),
                "enterprise_value": Decimal("1200"),
                "price_to_earnings": Decimal("20"),
                "price_to_sales": Decimal("5"),
                "price_to_book": Decimal("8"),
                "ev_to_ebitda": Decimal("15"),
                "free_cash_flow_yield": Decimal("0.04"),
                "earnings_yield": Decimal("0.05"),
                "company_profile_id": 1,
                "income_statement_id": 1,
                "balance_sheet_id": 1,
                "cash_flow_statement_id": 1,
                "missing_fields": [],
                "confidence": Decimal("1"),
            }
        ][:limit]


class FakeTTMFinancialsService:
    def __init__(self, db):
        self.db = db

    def get_ttm_financials(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return {
            "symbol": clean_symbol,
            "period_end_date": date(2026, 3, 31),
            "currency": "USD",
            "total_revenue": Decimal("1000"),
            "operating_income": Decimal("300"),
            "net_income": Decimal("250"),
            "ebitda": Decimal("350"),
            "free_cash_flow": Decimal("220"),
            "total_assets": Decimal("5000"),
            "stockholders_equity": Decimal("1500"),
            "cash_and_cash_equivalents": Decimal("500"),
            "total_debt": Decimal("1000"),
            "income_statement_ids": [1, 2, 3, 4],
            "balance_sheet_id": 1,
            "cash_flow_statement_ids": [1, 2, 3, 4],
            "quarter_end_dates": [
                date(2026, 3, 31),
                date(2025, 12, 31),
                date(2025, 9, 30),
                date(2025, 6, 30),
            ],
            "missing_fields": [],
            "confidence": Decimal("1"),
        }


class FakeTTMValuationMetricsService:
    def __init__(self, db):
        self.db = db

    def get_ttm_valuation_metrics(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return {
            "symbol": clean_symbol,
            "period_end_date": date(2026, 3, 31),
            "period_type": "ttm",
            "currency": "USD",
            "market_cap": Decimal("1000"),
            "enterprise_value": Decimal("1200"),
            "price_to_earnings": Decimal("20"),
            "price_to_sales": Decimal("5"),
            "price_to_book": Decimal("8"),
            "ev_to_ebitda": Decimal("15"),
            "free_cash_flow_yield": Decimal("0.04"),
            "earnings_yield": Decimal("0.05"),
            "company_profile_id": 1,
            "income_statement_ids": [1, 2, 3, 4],
            "balance_sheet_id": 1,
            "cash_flow_statement_ids": [1, 2, 3, 4],
            "quarter_end_dates": [
                date(2026, 3, 31),
                date(2025, 12, 31),
                date(2025, 9, 30),
                date(2025, 6, 30),
            ],
            "missing_fields": [],
            "confidence": Decimal("1"),
        }


def test_financial_metrics_endpoint_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.financial_metrics.FinancialMetricsService",
        FakeFinancialMetricsService,
    )

    response = client.get(
        "/financial-metrics/AAPL?period_type=annual&limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    assert body[0]["period_type"] == "annual"
    assert body[0]["operating_margin"] == "0.32"
    assert body[0]["confidence"] == "1"


def test_financial_metrics_endpoint_returns_404(monkeypatch):
    monkeypatch.setattr(
        "app.api.financial_metrics.FinancialMetricsService",
        FakeFinancialMetricsService,
    )

    response = client.get(
        "/financial-metrics/INVALID"
    )

    assert response.status_code == 404


def test_financial_metrics_rejects_invalid_limit():
    assert client.get(
        "/financial-metrics/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/financial-metrics/AAPL?limit=101"
    ).status_code == 422


def test_growth_metrics_endpoint_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.growth_metrics.GrowthMetricsService",
        FakeGrowthMetricsService,
    )

    response = client.get(
        "/growth-metrics/AAPL?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    assert body[0]["revenue_growth"] == "0.06"
    assert body[0]["confidence"] == "1"


def test_growth_metrics_endpoint_returns_404(monkeypatch):
    monkeypatch.setattr(
        "app.api.growth_metrics.GrowthMetricsService",
        FakeGrowthMetricsService,
    )

    response = client.get(
        "/growth-metrics/INVALID"
    )

    assert response.status_code == 404


def test_growth_metrics_rejects_invalid_limit():
    assert client.get(
        "/growth-metrics/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/growth-metrics/AAPL?limit=51"
    ).status_code == 422


def test_valuation_metrics_endpoint_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.valuation_metrics.ValuationMetricsService",
        FakeValuationMetricsService,
    )

    response = client.get(
        "/valuation-metrics/AAPL?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    assert body[0]["price_to_earnings"] == "20"
    assert body[0]["confidence"] == "1"


def test_valuation_metrics_endpoint_returns_404(monkeypatch):
    monkeypatch.setattr(
        "app.api.valuation_metrics.ValuationMetricsService",
        FakeValuationMetricsService,
    )

    response = client.get(
        "/valuation-metrics/INVALID"
    )

    assert response.status_code == 404


def test_valuation_metrics_rejects_invalid_limit():
    assert client.get(
        "/valuation-metrics/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/valuation-metrics/AAPL?limit=101"
    ).status_code == 422


def test_ttm_financials_endpoint_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.ttm_financials.TTMFinancialsService",
        FakeTTMFinancialsService,
    )

    response = client.get(
        "/ttm-financials/AAPL"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["total_revenue"] == "1000"
    assert body["confidence"] == "1"


def test_ttm_financials_endpoint_returns_404(monkeypatch):
    monkeypatch.setattr(
        "app.api.ttm_financials.TTMFinancialsService",
        FakeTTMFinancialsService,
    )

    response = client.get(
        "/ttm-financials/INVALID"
    )

    assert response.status_code == 404


def test_ttm_valuation_metrics_endpoint_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.ttm_valuation_metrics.TTMValuationMetricsService",
        FakeTTMValuationMetricsService,
    )

    response = client.get(
        "/ttm-valuation-metrics/AAPL"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["period_type"] == "ttm"
    assert body["price_to_earnings"] == "20"
    assert body["confidence"] == "1"


def test_ttm_valuation_metrics_endpoint_returns_404(monkeypatch):
    monkeypatch.setattr(
        "app.api.ttm_valuation_metrics.TTMValuationMetricsService",
        FakeTTMValuationMetricsService,
    )

    response = client.get(
        "/ttm-valuation-metrics/INVALID"
    )

    assert response.status_code == 404