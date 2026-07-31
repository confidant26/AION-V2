from sqlalchemy import select
from sqlalchemy.orm import Session

from app.mappers.market_price import MarketPriceMapper
from app.models.market_price import MarketPrice
from app.schemas.market_price import MarketPriceCreate


class MarketPriceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        price_data: MarketPriceCreate,
        asset_id: int,
    ) -> MarketPrice:
        market_price = MarketPriceMapper.to_model(
            data=price_data,
            asset_id=asset_id,
        )

        self.db.add(market_price)
        self.db.commit()
        self.db.refresh(market_price)

        return market_price

    def get_latest_by_asset_id(
        self,
        asset_id: int,
    ) -> MarketPrice | None:
        statement = (
            select(MarketPrice)
            .where(MarketPrice.asset_id == asset_id)
            .order_by(MarketPrice.timestamp.desc())
            .limit(1)
        )

        return self.db.scalar(statement)

    def list_by_asset_id(
        self,
        asset_id: int,
        limit: int = 100,
    ) -> list[MarketPrice]:
        statement = (
            select(MarketPrice)
            .where(MarketPrice.asset_id == asset_id)
            .order_by(MarketPrice.timestamp.desc())
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())