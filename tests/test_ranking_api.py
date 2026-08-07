from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ranking import RankingItem


client = TestClient(app)


def ranking_item(
    *,
    symbol: str,
    composite_score: str,
) -> RankingItem:
    return RankingItem(
        asset_id=1,
        symbol=symbol,
        name=f"{symbol} Company",
        asset_type="stock",
        exchange="NASDAQ",
        market="USA",
        currency="USD",
        country="US",
        sector="Technology",
        industry="Software",
        as_of_date=date(
            2026,
            6,
            30,
        ),
        growth_score=Decimal(
            "0.60"
        ),
        quality_score=Decimal(
            "0.80"
        ),
        valuation_score=Decimal(
            "0.50"
        ),
        composite_score=Decimal(
            composite_score
        ),
        confidence=Decimal(
            "1"
        ),
        period_alignment_ok=True,
        component_date_spread_days=273,
        missing_components=[],
    )


class FakeRankingService:
    def __init__(
        self,
        db,
    ):
        pass

    def get_ranking(
        self,
        *,
        offset=0,
        limit=50,
        min_confidence=Decimal("0"),
    ):
        results = [
            ranking_item(
                symbol="MSFT",
                composite_score="0.75",
            ),
            ranking_item(
                symbol="AAPL",
                composite_score="0.59",
            ),
        ]

        return (
            results[
                offset:
                offset + limit
            ],
            2,
        )

    def screen(
        self,
        **kwargs,
    ):
        return (
            [
                ranking_item(
                    symbol="MSFT",
                    composite_score="0.75",
                )
            ],
            1,
        )


def test_ranking_endpoint(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.ranking.RankingService",
        FakeRankingService,
    )

    response = client.get(
        "/ranking"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert body["count"] == 2

    assert (
        body["results"][0]["symbol"]
        == "MSFT"
    )

    assert (
        body["results"][1]["symbol"]
        == "AAPL"
    )


def test_ranking_pagination(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.ranking.RankingService",
        FakeRankingService,
    )

    response = client.get(
        "/ranking?offset=1&limit=1"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert body["count"] == 1

    assert (
        body["results"][0]["symbol"]
        == "AAPL"
    )


def test_screener_endpoint(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.ranking.RankingService",
        FakeRankingService,
    )

    response = client.get(
        "/screener"
        "?sector=Technology"
        "&min_composite_score=0.70"
        "&alignment_ok=true"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["count"] == 1

    assert (
        body["results"][0]["symbol"]
        == "MSFT"
    )


def test_screener_rejects_invalid_score():
    response = client.get(
        "/screener"
        "?min_composite_score=1.50"
    )

    assert response.status_code == 422