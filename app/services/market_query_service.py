from app.models.market_price import MarketPrice
from app.repositories.asset_repository import AssetRepository
from app.repositories.market_price_repository import MarketPriceRepository


class MarketQueryService:
    def __init__(
        self,
        asset_repository: AssetRepository,
        market_price_repository: MarketPriceRepository,
    ) -> None:
        self.asset_repository = asset_repository
        self.market_price_repository = market_price_repository

    def get_latest_price(self, symbol: str) -> MarketPrice:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise ValueError("Symbol cannot be empty.")

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found in database: {clean_symbol}"
            )

        latest_price = self.market_price_repository.get_latest_by_asset_id(
            asset.id
        )

        if latest_price is None:
            raise ValueError(
                f"Market price not found for asset: {clean_symbol}"
            )

        return latest_price

    def get_price_history(
        self,
        symbol: str,
        limit: int = 100,
    ) -> list[MarketPrice]:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise ValueError("Symbol cannot be empty.")

        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        if limit > 1000:
            raise ValueError("Limit cannot be greater than 1000.")

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found in database: {clean_symbol}"
            )

        prices = self.market_price_repository.list_by_asset_id(
            asset_id=asset.id,
            limit=limit,
        )

        if not prices:
            raise ValueError(
                f"Market price history not found for asset: {clean_symbol}"
            )

        return prices