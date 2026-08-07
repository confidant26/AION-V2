from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.watchlist import WatchlistItemResponse
from app.services.watchlist_service import (
    WatchlistAlreadyExistsError,
    WatchlistAssetNotFoundError,
    WatchlistItemNotFoundError,
)


client = TestClient(app)


def watchlist_item() -> WatchlistItemResponse:
    return WatchlistItemResponse(
        id=1,
        asset_id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        market="USA",
        currency="USD",
        country="US",
        sector="Technology",
        industry="Consumer Electronics",
        created_at=datetime(
            2026,
            8,
            7,
            tzinfo=timezone.utc,
        ),
    )


class FakeWatchlistService:
    def __init__(
        self,
        db,
    ):
        pass

    def add(
        self,
        symbol,
    ):
        return watchlist_item()

    def list_items(
        self,
    ):
        return [
            watchlist_item()
        ]

    def get(
        self,
        symbol,
    ):
        return watchlist_item()

    def remove(
        self,
        symbol,
    ):
        return symbol.strip().upper()


class FakeMissingWatchlistService:
    def __init__(
        self,
        db,
    ):
        pass

    def add(
        self,
        symbol,
    ):
        raise WatchlistAssetNotFoundError(
            "Asset not found for symbol: INVALID"
        )

    def get(
        self,
        symbol,
    ):
        raise WatchlistItemNotFoundError(
            "Watchlist item not found for symbol: INVALID"
        )

    def remove(
        self,
        symbol,
    ):
        raise WatchlistItemNotFoundError(
            "Watchlist item not found for symbol: INVALID"
        )


class FakeDuplicateWatchlistService:
    def __init__(
        self,
        db,
    ):
        pass

    def add(
        self,
        symbol,
    ):
        raise WatchlistAlreadyExistsError(
            "Asset already exists in watchlist: AAPL"
        )


def test_add_to_watchlist(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.watchlist.WatchlistService",
        FakeWatchlistService,
    )

    response = client.post(
        "/watchlist/aapl"
    )

    assert response.status_code == 201

    assert response.json()["symbol"] == "AAPL"


def test_list_watchlist(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.watchlist.WatchlistService",
        FakeWatchlistService,
    )

    response = client.get(
        "/watchlist"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1

    assert (
        response.json()["results"][0]["symbol"]
        == "AAPL"
    )


def test_get_watchlist_item(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.watchlist.WatchlistService",
        FakeWatchlistService,
    )

    response = client.get(
        "/watchlist/AAPL"
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"


def test_remove_from_watchlist(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.watchlist.WatchlistService",
        FakeWatchlistService,
    )

    response = client.delete(
        "/watchlist/aapl"
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"


def test_watchlist_missing_asset_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.watchlist.WatchlistService",
        FakeMissingWatchlistService,
    )

    response = client.post(
        "/watchlist/INVALID"
    )

    assert response.status_code == 404


def test_duplicate_watchlist_item_returns_409(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.watchlist.WatchlistService",
        FakeDuplicateWatchlistService,
    )

    response = client.post(
        "/watchlist/AAPL"
    )

    assert response.status_code == 409