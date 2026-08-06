from types import SimpleNamespace

import pytest

from app.services.market_ingestion_service import (
    MarketIngestionService,
)
from app.services.market_query_service import (
    MarketQueryService,
)


class FakeAssetRepository:
    def __init__(
        self,
        asset=None,
    ):
        self.asset = asset
        self.requested_symbols = []

    def get_by_symbol(
        self,
        symbol: str,
    ):
        self.requested_symbols.append(
            symbol
        )

        return self.asset


class FakeMarketPriceRepository:
    def __init__(
        self,
        *,
        created_price=None,
        latest_price=None,
        history=None,
    ):
        self.created_price = created_price
        self.latest_price = latest_price
        self.history = (
            history
            if history is not None
            else []
        )

        self.created_calls = []
        self.latest_asset_ids = []
        self.history_calls = []

    def create(
        self,
        *,
        price_data,
        asset_id: int,
    ):
        self.created_calls.append(
            {
                "price_data": price_data,
                "asset_id": asset_id,
            }
        )

        return self.created_price

    def get_latest_by_asset_id(
        self,
        asset_id: int,
    ):
        self.latest_asset_ids.append(
            asset_id
        )

        return self.latest_price

    def list_by_asset_id(
        self,
        *,
        asset_id: int,
        limit: int,
    ):
        self.history_calls.append(
            {
                "asset_id": asset_id,
                "limit": limit,
            }
        )

        return self.history


class FakeMarketDataService:
    def __init__(
        self,
        price_data,
    ):
        self.price_data = price_data
        self.requested_symbols = []

    async def get_latest_price(
        self,
        symbol: str,
    ):
        self.requested_symbols.append(
            symbol
        )

        return self.price_data


@pytest.mark.anyio
@pytest.mark.parametrize(
    "symbol",
    [
        "",
        " ",
        "   ",
    ],
)
async def test_market_ingestion_rejects_empty_symbol(
    symbol,
):
    service = object.__new__(
        MarketIngestionService
    )

    service.asset_repository = (
        FakeAssetRepository()
    )
    service.market_price_repository = (
        FakeMarketPriceRepository()
    )
    service.market_data_service = (
        FakeMarketDataService(
            price_data=None
        )
    )

    with pytest.raises(
        ValueError,
        match="Symbol cannot be empty.",
    ):
        await service.collect_and_save_latest_price(
            symbol
        )


@pytest.mark.anyio
async def test_market_ingestion_normalizes_symbol_and_saves_price():
    asset = SimpleNamespace(
        id=7,
        symbol="AAPL",
    )

    price_data = SimpleNamespace(
        close_price=203.5,
    )

    saved_price = SimpleNamespace(
        id=99,
        asset_id=7,
        close_price=203.5,
    )

    asset_repository = (
        FakeAssetRepository(
            asset=asset
        )
    )

    market_price_repository = (
        FakeMarketPriceRepository(
            created_price=saved_price
        )
    )

    market_data_service = (
        FakeMarketDataService(
            price_data=price_data
        )
    )

    service = object.__new__(
        MarketIngestionService
    )

    service.asset_repository = (
        asset_repository
    )
    service.market_price_repository = (
        market_price_repository
    )
    service.market_data_service = (
        market_data_service
    )

    result = (
        await service
        .collect_and_save_latest_price(
            "  aapl  "
        )
    )

    assert result is saved_price

    assert (
        asset_repository
        .requested_symbols
        == ["AAPL"]
    )

    assert (
        market_data_service
        .requested_symbols
        == ["AAPL"]
    )

    assert (
        market_price_repository
        .created_calls
        == [
            {
                "price_data": price_data,
                "asset_id": 7,
            }
        ]
    )


@pytest.mark.anyio
async def test_market_ingestion_fails_when_asset_is_missing():
    asset_repository = (
        FakeAssetRepository(
            asset=None
        )
    )

    service = object.__new__(
        MarketIngestionService
    )

    service.asset_repository = (
        asset_repository
    )
    service.market_price_repository = (
        FakeMarketPriceRepository()
    )
    service.market_data_service = (
        FakeMarketDataService(
            price_data=None
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Asset not found in database: AAPL"
        ),
    ):
        await service.collect_and_save_latest_price(
            "aapl"
        )


@pytest.mark.parametrize(
    "symbol",
    [
        "",
        " ",
        "   ",
    ],
)
def test_market_query_latest_rejects_empty_symbol(
    symbol,
):
    service = MarketQueryService(
        asset_repository=FakeAssetRepository(),
        market_price_repository=(
            FakeMarketPriceRepository()
        ),
    )

    with pytest.raises(
        ValueError,
        match="Symbol cannot be empty.",
    ):
        service.get_latest_price(
            symbol
        )


def test_market_query_latest_fails_when_asset_is_missing():
    service = MarketQueryService(
        asset_repository=(
            FakeAssetRepository(
                asset=None
            )
        ),
        market_price_repository=(
            FakeMarketPriceRepository()
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Asset not found in database: AAPL"
        ),
    ):
        service.get_latest_price(
            "aapl"
        )


def test_market_query_latest_fails_when_price_is_missing():
    asset = SimpleNamespace(
        id=7,
    )

    service = MarketQueryService(
        asset_repository=(
            FakeAssetRepository(
                asset=asset
            )
        ),
        market_price_repository=(
            FakeMarketPriceRepository(
                latest_price=None
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Market price not found for asset: AAPL"
        ),
    ):
        service.get_latest_price(
            "AAPL"
        )


def test_market_query_latest_returns_price():
    asset = SimpleNamespace(
        id=7,
    )

    latest_price = SimpleNamespace(
        id=15,
        asset_id=7,
        close_price=203.5,
    )

    asset_repository = (
        FakeAssetRepository(
            asset=asset
        )
    )

    market_price_repository = (
        FakeMarketPriceRepository(
            latest_price=latest_price
        )
    )

    service = MarketQueryService(
        asset_repository=asset_repository,
        market_price_repository=(
            market_price_repository
        ),
    )

    result = service.get_latest_price(
        "  aapl "
    )

    assert result is latest_price

    assert (
        asset_repository
        .requested_symbols
        == ["AAPL"]
    )

    assert (
        market_price_repository
        .latest_asset_ids
        == [7]
    )


@pytest.mark.parametrize(
    "limit, expected_message",
    [
        (
            0,
            "Limit must be greater than zero.",
        ),
        (
            -1,
            "Limit must be greater than zero.",
        ),
        (
            1001,
            "Limit cannot be greater than 1000.",
        ),
    ],
)
def test_market_query_history_rejects_invalid_limit(
    limit,
    expected_message,
):
    service = MarketQueryService(
        asset_repository=FakeAssetRepository(),
        market_price_repository=(
            FakeMarketPriceRepository()
        ),
    )

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        service.get_price_history(
            symbol="AAPL",
            limit=limit,
        )


def test_market_query_history_fails_when_asset_is_missing():
    service = MarketQueryService(
        asset_repository=(
            FakeAssetRepository(
                asset=None
            )
        ),
        market_price_repository=(
            FakeMarketPriceRepository()
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Asset not found in database: AAPL"
        ),
    ):
        service.get_price_history(
            symbol="aapl",
            limit=100,
        )


def test_market_query_history_fails_when_history_is_empty():
    asset = SimpleNamespace(
        id=7,
    )

    service = MarketQueryService(
        asset_repository=(
            FakeAssetRepository(
                asset=asset
            )
        ),
        market_price_repository=(
            FakeMarketPriceRepository(
                history=[]
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Market price history not found for asset: AAPL"
        ),
    ):
        service.get_price_history(
            symbol="AAPL",
            limit=100,
        )


def test_market_query_history_returns_prices_and_passes_limit():
    asset = SimpleNamespace(
        id=7,
    )

    prices = [
        SimpleNamespace(
            id=1,
        ),
        SimpleNamespace(
            id=2,
        ),
    ]

    asset_repository = (
        FakeAssetRepository(
            asset=asset
        )
    )

    market_price_repository = (
        FakeMarketPriceRepository(
            history=prices
        )
    )

    service = MarketQueryService(
        asset_repository=asset_repository,
        market_price_repository=(
            market_price_repository
        ),
    )

    result = service.get_price_history(
        symbol="  aapl ",
        limit=25,
    )

    assert result == prices

    assert (
        asset_repository
        .requested_symbols
        == ["AAPL"]
    )

    assert (
        market_price_repository
        .history_calls
        == [
            {
                "asset_id": 7,
                "limit": 25,
            }
        ]
    )