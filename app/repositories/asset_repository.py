from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.schemas.asset import AssetCreate


class AssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, asset_id: int) -> Asset | None:
        statement = select(Asset).where(Asset.id == asset_id)

        return self.db.scalar(statement)

    def get_by_symbol(self, symbol: str) -> Asset | None:
        statement = select(Asset).where(Asset.symbol == symbol)

        return self.db.scalar(statement)

    def list_assets(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[Asset]:
        statement = (
            select(Asset)
            .order_by(Asset.symbol.asc())
            .offset(offset)
            .limit(limit)
        )

        if active_only:
            statement = statement.where(Asset.active.is_(True))

        return list(self.db.scalars(statement).all())

    def create(self, asset_data: AssetCreate) -> Asset:
        asset = Asset(
            **asset_data.model_dump(mode="json"),
        )

        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        return asset