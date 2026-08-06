from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.db.dependencies import get_db
from app.main import app
from app.services.asset_service import (
    AssetAlreadyExistsError,
    AssetNotFoundError,
)


class FakeDB:
    pass


def override_get_db():
    yield FakeDB()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


NOW = datetime(
    2026,
    8,
    6,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_asset(
    *,
    asset_id: int = 1,
    symbol: str = "AAPL",
):
    return SimpleNamespace(
        id=asset_id,
        symbol=symbol,
        name="Apple Inc.",
        asset_type="stock",
        exchange="NASDAQ",
        market="US",
        currency="USD",
        country="US",
        sector="Technology",
        industry="Consumer Electronics",
        isin="US0378331005",
        active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def make_company_profile():
    return SimpleNamespace(
        id=1,
        asset_id=1,
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        country="US",
        currency="USD",
        market_cap=3_000_000_000_000,
        full_time_employees=160000,
        website="https://www.apple.com",
        description="Technology company.",
    )


def make_market_price(
    *,
    price_id: int = 1,
):
    return SimpleNamespace(
        id=price_id,
        asset_id=1,
        open_price=200.0,
        high_price=205.0,
        low_price=198.0,
        close_price=203.5,
        volume=50_000_000,
        timestamp=NOW,
        created_at=NOW,
    )


class FakeCompanyProfileService:
    def __init__(
        self,
        db,
        provider,
    ):
        self.db = db
        self.provider = provider

    def get_company_profile(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Company profile not found for symbol: INVALID"
            )

        return make_company_profile()

    async def collect_company_profile(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Company profile not found for symbol: INVALID"
            )

        return make_company_profile()


class FakeAssetService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def create_asset(
        self,
        asset_data,
    ):
        if asset_data.symbol == "EXISTS":
            raise AssetAlreadyExistsError(
                "Asset already exists: EXISTS"
            )

        return make_asset(
            symbol=asset_data.symbol,
        )

    def list_assets(
        self,
        *,
        offset: int,
        limit: int,
        active_only: bool,
    ):
        return [
            make_asset(
                asset_id=1,
                symbol="AAPL",
            ),
            make_asset(
                asset_id=2,
                symbol="MSFT",
            ),
        ][offset:offset + limit]

    def get_asset(
        self,
        asset_id: int,
    ):
        if asset_id == 999:
            raise AssetNotFoundError(
                "Asset not found: 999"
            )

        return make_asset(
            asset_id=asset_id,
        )


class FakeMarketIngestionService:
    def __init__(
        self,
        asset_repository,
        market_price_repository,
    ):
        self.asset_repository = asset_repository
        self.market_price_repository = (
            market_price_repository
        )

    async def collect_and_save_latest_price(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return make_market_price()


class FakeMarketQueryService:
    def __init__(
        self,
        asset_repository,
        market_price_repository,
    ):
        self.asset_repository = asset_repository
        self.market_price_repository = (
            market_price_repository
        )

    def get_latest_price(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return make_market_price()

    def get_price_history(
        self,
        symbol: str,
        limit: int = 100,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        prices = [
            make_market_price(
                price_id=1,
            ),
            make_market_price(
                price_id=2,
            ),
        ]

        return prices[:limit]


def patch_company_dependencies(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.company.CompanyProfileService",
        FakeCompanyProfileService,
    )

    monkeypatch.setattr(
        "app.api.company.get_company_data_provider",
        lambda: object(),
    )


def patch_market_dependencies(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.market.AssetRepository",
        lambda db: object(),
    )

    monkeypatch.setattr(
        "app.api.market.MarketPriceRepository",
        lambda db: object(),
    )

    monkeypatch.setattr(
        "app.api.market.MarketIngestionService",
        FakeMarketIngestionService,
    )

    monkeypatch.setattr(
        "app.api.market.MarketQueryService",
        FakeMarketQueryService,
    )


def test_company_get_success(
    monkeypatch,
):
    patch_company_dependencies(
        monkeypatch
    )

    response = client.get(
        "/company/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == 1
    assert body["asset_id"] == 1
    assert body["symbol"] == "AAPL"
    assert body["company_name"] == "Apple Inc."
    assert body["sector"] == "Technology"
    assert body["currency"] == "USD"
    assert body["market_cap"] == 3_000_000_000_000


def test_company_get_returns_404(
    monkeypatch,
):
    patch_company_dependencies(
        monkeypatch
    )

    response = client.get(
        "/company/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Company profile not found for symbol: INVALID"
        )
    }


def test_company_collect_success(
    monkeypatch,
):
    patch_company_dependencies(
        monkeypatch
    )

    response = client.post(
        "/company/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == (
        "Company profile collected successfully."
    )
    assert body["symbol"] == "AAPL"
    assert body["company_name"] == "Apple Inc."
    assert body["asset_id"] == 1


def test_company_collect_returns_404(
    monkeypatch,
):
    patch_company_dependencies(
        monkeypatch
    )

    response = client.post(
        "/company/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Company profile not found for symbol: INVALID"
        )
    }


def test_create_asset_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetService",
        FakeAssetService,
    )

    response = client.post(
        "/assets",
        json={
            "symbol": " aapl ",
            "name": " Apple Inc. ",
            "asset_type": "stock",
            "exchange": "nasdaq",
            "market": "us",
            "currency": "usd",
            "country": "us",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "isin": "us0378331005",
            "active": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == 1
    assert body["symbol"] == "AAPL"
    assert body["asset_type"] == "stock"
    assert body["exchange"] == "NASDAQ"
    assert body["currency"] == "USD"
    assert body["active"] is True


def test_create_asset_returns_409(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetService",
        FakeAssetService,
    )

    response = client.post(
        "/assets",
        json={
            "symbol": "EXISTS",
            "name": "Existing Asset",
            "asset_type": "stock",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Asset already exists: EXISTS"
        )
    }


def test_list_assets_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetService",
        FakeAssetService,
    )

    response = client.get(
        "/assets?offset=0&limit=10&active_only=true"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert body[0]["symbol"] == "AAPL"
    assert body[1]["symbol"] == "MSFT"


def test_list_assets_rejects_invalid_query():
    assert client.get(
        "/assets?offset=-1"
    ).status_code == 422

    assert client.get(
        "/assets?limit=0"
    ).status_code == 422

    assert client.get(
        "/assets?limit=501"
    ).status_code == 422


def test_get_asset_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetService",
        FakeAssetService,
    )

    response = client.get(
        "/assets/1"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == 1
    assert body["symbol"] == "AAPL"
    assert body["name"] == "Apple Inc."


def test_get_asset_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.assets.AssetService",
        FakeAssetService,
    )

    response = client.get(
        "/assets/999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Asset not found: 999"
    }


def test_market_collect_success(
    monkeypatch,
):
    patch_market_dependencies(
        monkeypatch
    )

    response = client.post(
        "/market/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == (
        "Market price collected successfully."
    )
    assert body["id"] == 1
    assert body["asset_id"] == 1
    assert body["open"] == 200.0
    assert body["close"] == 203.5
    assert body["volume"] == 50_000_000


def test_market_collect_returns_404(
    monkeypatch,
):
    patch_market_dependencies(
        monkeypatch
    )

    response = client.post(
        "/market/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_market_latest_success(
    monkeypatch,
):
    patch_market_dependencies(
        monkeypatch
    )

    response = client.get(
        "/market/latest/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == 1
    assert body["asset_id"] == 1
    assert body["symbol"] == "AAPL"
    assert body["close"] == 203.5
    assert body["volume"] == 50_000_000


def test_market_latest_returns_404(
    monkeypatch,
):
    patch_market_dependencies(
        monkeypatch
    )

    response = client.get(
        "/market/latest/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_market_history_success(
    monkeypatch,
):
    patch_market_dependencies(
        monkeypatch
    )

    response = client.get(
        "/market/history/aapl?limit=2"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["count"] == 2
    assert body["limit"] == 2

    assert body["prices"][0]["id"] == 1
    assert body["prices"][0]["close"] == 203.5
    assert body["prices"][1]["id"] == 2


def test_market_history_returns_404(
    monkeypatch,
):
    patch_market_dependencies(
        monkeypatch
    )

    response = client.get(
        "/market/history/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_market_history_rejects_invalid_limit():
    assert client.get(
        "/market/history/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/market/history/AAPL?limit=1001"
    ).status_code == 422