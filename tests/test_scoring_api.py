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


class FakeGrowthScoreService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def get_growth_scores(
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
                "revenue_growth_score": Decimal("0.50"),
                "operating_income_growth_score": Decimal(
                    "0.50"
                ),
                "net_income_growth_score": Decimal("0.75"),
                "free_cash_flow_growth_score": Decimal(
                    "0.25"
                ),
                "total_assets_growth_score": Decimal(
                    "0.25"
                ),
                "stockholders_equity_growth_score": Decimal(
                    "1"
                ),
                "growth_score": Decimal(
                    "0.5416666666666666666666666667"
                ),
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


class FakeQualityScoreService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def get_quality_scores(
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
                "period_type": "annual",
                "currency": "USD",
                "profitability_score": Decimal("1"),
                "balance_sheet_score": Decimal("0.50"),
                "cash_flow_score": Decimal("1"),
                "quality_score": Decimal(
                    "0.8333333333333333333333333333"
                ),
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


class FakeValuationScoreService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def get_valuation_score(
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
            "earnings_yield_score": Decimal("0.25"),
            "free_cash_flow_yield_score": Decimal("0.50"),
            "valuation_score": Decimal("0.375"),
            "market_cap": Decimal("4897204862976"),
            "enterprise_value": Decimal(
                "4913408862976"
            ),
            "price_to_earnings": Decimal("39.95"),
            "price_to_sales": Decimal("10.85"),
            "price_to_book": Decimal("45.99"),
            "ev_to_ebitda": Decimal("30.71"),
            "free_cash_flow_yield": Decimal("0.026"),
            "earnings_yield": Decimal("0.025"),
            "company_profile_id": 1,
            "income_statement_ids": [
                6,
                7,
                8,
                9,
            ],
            "balance_sheet_id": 6,
            "cash_flow_statement_ids": [
                7,
                8,
                9,
                10,
            ],
            "quarter_end_dates": [
                date(2026, 3, 31),
                date(2025, 12, 31),
                date(2025, 9, 30),
                date(2025, 6, 30),
            ],
            "missing_fields": [],
            "confidence": Decimal("1"),
        }


def test_growth_score_endpoint_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.growth_score.GrowthScoreService",
        FakeGrowthScoreService,
    )

    response = client.get(
        "/growth-score/AAPL?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    assert body[0]["period_type"] == "annual"
    assert body[0]["growth_score"] == (
        "0.5416666666666666666666666667"
    )
    assert body[0]["confidence"] == "1"


def test_growth_score_endpoint_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.growth_score.GrowthScoreService",
        FakeGrowthScoreService,
    )

    response = client.get(
        "/growth-score/INVALID"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_growth_score_rejects_limit_below_one():
    response = client.get(
        "/growth-score/AAPL?limit=0"
    )

    assert response.status_code == 422


def test_growth_score_rejects_limit_above_fifty():
    response = client.get(
        "/growth-score/AAPL?limit=51"
    )

    assert response.status_code == 422


def test_quality_score_endpoint_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.quality_score.QualityScoreService",
        FakeQualityScoreService,
    )

    response = client.get(
        "/quality-score/AAPL?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    assert body[0]["period_type"] == "annual"
    assert body[0]["quality_score"] == (
        "0.8333333333333333333333333333"
    )
    assert body[0]["confidence"] == "1"


def test_quality_score_endpoint_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.quality_score.QualityScoreService",
        FakeQualityScoreService,
    )

    response = client.get(
        "/quality-score/INVALID"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_quality_score_rejects_limit_below_one():
    response = client.get(
        "/quality-score/AAPL?limit=0"
    )

    assert response.status_code == 422


def test_quality_score_rejects_limit_above_fifty():
    response = client.get(
        "/quality-score/AAPL?limit=51"
    )

    assert response.status_code == 422


def test_valuation_score_endpoint_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.valuation_score.ValuationScoreService",
        FakeValuationScoreService,
    )

    response = client.get(
        "/valuation-score/AAPL"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["period_type"] == "ttm"
    assert body["earnings_yield_score"] == "0.25"
    assert body["free_cash_flow_yield_score"] == "0.50"
    assert body["valuation_score"] == "0.375"
    assert body["confidence"] == "1"


def test_valuation_score_endpoint_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.valuation_score.ValuationScoreService",
        FakeValuationScoreService,
    )

    response = client.get(
        "/valuation-score/INVALID"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }