from app.providers.market.factory import MarketProviderFactory
from app.schemas.market_price import MarketPriceCreate


class MarketDataService:
    def __init__(self, provider_name: str | None = None) -> None:
        self.provider = MarketProviderFactory.create(provider_name)

    async def get_latest_price(self, symbol: str) -> MarketPriceCreate:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise ValueError("Symbol cannot be empty.")

        raw_data = await self.provider.get_latest_price(clean_symbol)

        return MarketPriceCreate.model_validate(raw_data)
