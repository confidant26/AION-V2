from app.models.market_price import MarketPrice
from app.repositories.asset_repository import AssetRepository
from app.repositories.market_price_repository import MarketPriceRepository
from app.services.market_data_service import MarketDataService


class MarketIngestionService:
    def __init__(
        self,
        asset_repository: AssetRepository,
        market_price_repository: MarketPriceRepository,
        provider_name: str = "yahoo",
    ) -> None:
        self.asset_repository = asset_repository
        self.market_price_repository = market_price_repository
        self.market_data_service = MarketDataService(provider_name)

    async def collect_and_save_latest_price(
        self,
        symbol: str,
    ) -> MarketPrice:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise ValueError("Symbol cannot be empty.")

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found in database: {clean_symbol}"
            )

        price_data = await self.market_data_service.get_latest_price(
            clean_symbol
        )

        return self.market_price_repository.create(
            price_data=price_data,
            asset_id=asset.id,
        )