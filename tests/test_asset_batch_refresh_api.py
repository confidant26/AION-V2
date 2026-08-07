from fastapi.testclient import TestClient

from app.main import app
from app.schemas.asset_batch_refresh import (
    AssetBatchRefreshItem,
    AssetBatchRefreshResponse,
)


client = TestClient(
    app
)


class FakeAssetBatchRefreshService:
    def __init__(
        self,
    ):
        pass

    async def refresh_many(
        self,
        *,
        symbols,
        include_analysis=False,
        concurrency=3,
    ):
        results = []

        for symbol in symbols:
            if symbol == "INVALID":
                results.append(
                    AssetBatchRefreshItem(
                        symbol=symbol,
                        success=False,
                        result=None,
                        error=(
                            "Asset not found for "
                            "symbol: INVALID"
                        ),
                    )
                )

                continue

            result = {
                "symbol": symbol,
                "status": "healthy",
            }

            if include_analysis:
                result["analysis"] = {
                    "composite_score": {
                        "symbol": symbol,
                    }
                }

            results.append(
                AssetBatchRefreshItem(
                    symbol=symbol,
                    success=True,
                    result=result,
                    error=None,
                )
            )

        success_count = sum(
            1
            for item in results
            if item.success
        )

        return AssetBatchRefreshResponse(
            requested_count=len(
                results
            ),
            success_count=(
                success_count
            ),
            failed_count=(
                len(results)
                - success_count
            ),
            results=results,
        )


def test_batch_refresh_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets."
        "AssetBatchRefreshService",
        FakeAssetBatchRefreshService,
    )

    response = client.post(
        "/assets/refresh-batch",
        json={
            "symbols": [
                "AAPL",
                "MSFT",
            ],
            "include_analysis": False,
            "concurrency": 2,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["requested_count"]
        == 2
    )

    assert (
        body["success_count"]
        == 2
    )

    assert (
        body["failed_count"]
        == 0
    )

    assert (
        body["results"][0]["symbol"]
        == "AAPL"
    )

    assert (
        body["results"][1]["symbol"]
        == "MSFT"
    )


def test_batch_refresh_partial_failure(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets."
        "AssetBatchRefreshService",
        FakeAssetBatchRefreshService,
    )

    response = client.post(
        "/assets/refresh-batch",
        json={
            "symbols": [
                "AAPL",
                "INVALID",
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["requested_count"]
        == 2
    )

    assert (
        body["success_count"]
        == 1
    )

    assert (
        body["failed_count"]
        == 1
    )

    assert (
        body["results"][0]["success"]
        is True
    )

    assert (
        body["results"][1]["success"]
        is False
    )

    assert (
        "Asset not found"
        in body["results"][1]["error"]
    )


def test_batch_refresh_normalizes_and_deduplicates(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets."
        "AssetBatchRefreshService",
        FakeAssetBatchRefreshService,
    )

    response = client.post(
        "/assets/refresh-batch",
        json={
            "symbols": [
                " aapl ",
                "AAPL",
                " msft ",
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["requested_count"]
        == 2
    )

    assert [
        item["symbol"]
        for item in body["results"]
    ] == [
        "AAPL",
        "MSFT",
    ]


def test_batch_refresh_with_analysis(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets."
        "AssetBatchRefreshService",
        FakeAssetBatchRefreshService,
    )

    response = client.post(
        "/assets/refresh-batch",
        json={
            "symbols": [
                "AAPL",
            ],
            "include_analysis": True,
        },
    )

    assert response.status_code == 200

    result = (
        response.json()[
            "results"
        ][0]
    )

    assert (
        result["result"][
            "analysis"
        ][
            "composite_score"
        ][
            "symbol"
        ]
        == "AAPL"
    )


def test_batch_refresh_rejects_empty_symbols():
    response = client.post(
        "/assets/refresh-batch",
        json={
            "symbols": [],
        },
    )

    assert response.status_code == 422


def test_batch_refresh_rejects_invalid_concurrency():
    response = client.post(
        "/assets/refresh-batch",
        json={
            "symbols": [
                "AAPL",
            ],
            "concurrency": 20,
        },
    )

    assert response.status_code == 422