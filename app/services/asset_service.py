from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate


class AssetAlreadyExistsError(Exception):
    pass


class AssetNotFoundError(Exception):
    pass


class AssetService:
    def __init__(self, db: Session) -> None:
        self.repository = AssetRepository(db)

    def create_asset(self, asset_data: AssetCreate) -> Asset:
        existing_asset = self.repository.get_by_symbol(asset_data.symbol)

        if existing_asset is not None:
            raise AssetAlreadyExistsError(
                f"{asset_data.symbol} sembolüne sahip varlık zaten mevcut."
            )

        try:
            return self.repository.create(asset_data)
        except IntegrityError as exc:
            self.repository.db.rollback()

            raise AssetAlreadyExistsError(
                "Aynı symbol veya ISIN değerine sahip bir varlık zaten mevcut."
            ) from exc

    def get_asset(self, asset_id: int) -> Asset:
        asset = self.repository.get_by_id(asset_id)

        if asset is None:
            raise AssetNotFoundError(
                f"{asset_id} kimlik numaralı varlık bulunamadı."
            )

        return asset

    def list_assets(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[Asset]:
        return self.repository.list_assets(
            offset=offset,
            limit=limit,
            active_only=active_only,
        )