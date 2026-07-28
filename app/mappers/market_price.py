from datetime import timezone

from app.models.market_price import MarketPrice
from app.schemas.market_price import MarketPriceCreate


class MarketPriceMapper:
    @staticmethod
    def to_model(
        data: MarketPriceCreate,
        asset_id: int,
    ) -> MarketPrice:
        if asset_id <= 0:
            raise ValueError("asset_id must be greater than zero.")

        timestamp = data.timestamp

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return MarketPrice(
            asset_id=asset_id,
            open_price=data.open,
            high_price=data.high,
            low_price=data.low,
            close_price=data.close,
            volume=data.volume,
            timestamp=timestamp,
        )