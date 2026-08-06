from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class FakeAssetRefreshService:
    def __init__(
        self,
        db,
    ):
        pass

    async def refresh(
        self,
        *,
        symbol,
        include_analysis=False,
    ):
        response = {
            "message": (
                "Asset refreshed successfully."
            ),
            "symbol": symbol.strip().upper(),
            "status": "healthy",
            "warnings": [],
            "company_profile": {
                "company_name": "Apple Inc.",
            },
            "market_price": {
                "close": "200",
            },
            "financials": {
                "counts": {
                    "income_statements": 9,
                    "balance_sheets": 9,
                    "cash_flow_statements": 9,
                },
                "total_count": 27,
                "latest_quarterly_periods": {
                    "income_statements": "2026-06-30",
                    "balance_sheets": "2026-06-30",
                    "cash_flow_statements": "2026-06-30",
                },
                "quarterly_alignment": {
                    "ok": True,
                    "spread_days": 0,
                },
            },
        }

        if include_analysis:
            response["analysis"] = {
                "ttm_financials": {
                    "symbol": "AAPL",
                },
                "ttm_valuation_metrics": {
                    "symbol": "AAPL",
                },
                "composite_score": {
                    "symbol": "AAPL",
                    "composite_score": "0.59",
                },
            }

        return response


class FakeMissingAssetRefreshService:
    def __init__(
        self,
        db,
    ):
        pass

    async def refresh(
        self,
        *,
        symbol,
        include_analysis=False,
    ):
        raise ValueError(
            f"Asset not found for symbol: "
            f"{symbol.strip().upper()}"
        )


def test_asset_refresh_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetRefreshService",
        FakeAssetRefreshService,
    )

    response = client.post(
        "/assets/refresh/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["status"] == "healthy"

    assert (
        body["financials"][
            "quarterly_alignment"
        ]["ok"]
        is True
    )

    assert "analysis" not in body


def test_asset_refresh_with_analysis(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetRefreshService",
        FakeAssetRefreshService,
    )

    response = client.post(
        "/assets/refresh/aapl"
        "?include_analysis=true"
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["analysis"][
            "ttm_financials"
        ]["symbol"]
        == "AAPL"
    )

    assert (
        body["analysis"][
            "ttm_valuation_metrics"
        ]["symbol"]
        == "AAPL"
    )

    assert (
        body["analysis"][
            "composite_score"
        ]["composite_score"]
        == "0.59"
    )


def test_asset_refresh_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetRefreshService",
        FakeMissingAssetRefreshService,
    )

    response = client.post(
        "/assets/refresh/INVALID"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Asset not found for symbol: INVALID"
    )