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


class FakeCompositeScoreService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def get_composite_score(
        self,
        symbol: str,
    ):
        if symbol.strip().upper() == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return {
            "symbol": "AAPL",
            "as_of_date": date(2026, 3, 31),
            "currency": "USD",
            "growth_score": Decimal(
                "0.5416666666666666666666666667"
            ),
            "quality_score": Decimal(
                "0.8333333333333333333333333333"
            ),
            "valuation_score": Decimal("0.375"),
            "composite_score": Decimal("0.59375"),
            "growth_weight": Decimal("0.35"),
            "quality_weight": Decimal("0.35"),
            "valuation_weight": Decimal("0.30"),
            "growth_period_end_date": date(
                2025,
                9,
                30,
            ),
            "quality_period_end_date": date(
                2025,
                9,
                30,
            ),
            "valuation_period_end_date": date(
                2026,
                3,
                31,
            ),
            "oldest_component_date": date(
                2025,
                9,
                30,
            ),
            "newest_component_date": date(
                2026,
                3,
                31,
            ),
            "component_date_spread_days": 182,
            "period_alignment_ok": True,
            "missing_components": [],
            "confidence": Decimal("1"),
        }


def test_composite_score_endpoint_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.composite_score.CompositeScoreService",
        FakeCompositeScoreService,
    )

    response = client.get(
        "/composite-score/AAPL"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["composite_score"] == "0.59375"
    assert body["growth_weight"] == "0.35"
    assert body["quality_weight"] == "0.35"
    assert body["valuation_weight"] == "0.30"
    assert body["component_date_spread_days"] == 182
    assert body["period_alignment_ok"] is True
    assert body["missing_components"] == []
    assert body["confidence"] == "1"


def test_composite_score_endpoint_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.composite_score.CompositeScoreService",
        FakeCompositeScoreService,
    )

    response = client.get(
        "/composite-score/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }