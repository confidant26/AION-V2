from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import WatchlistItemResponse


class WatchlistAssetNotFoundError(Exception):
    pass


class WatchlistAlreadyExistsError(Exception):
    pass


class WatchlistItemNotFoundError(Exception):
    pass


class WatchlistService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.asset_repository = (
            AssetRepository(db)
        )

        self.watchlist_repository = (
            WatchlistRepository(db)
        )

    @staticmethod
    def _serialize(
        item,
    ) -> WatchlistItemResponse:
        asset = item.asset

        return WatchlistItemResponse(
            id=item.id,
            asset_id=item.asset_id,
            symbol=asset.symbol,
            name=asset.name,
            asset_type=asset.asset_type,
            exchange=asset.exchange,
            market=asset.market,
            currency=asset.currency,
            country=asset.country,
            sector=asset.sector,
            industry=asset.industry,
            created_at=item.created_at,
        )

    def add(
        self,
        symbol: str,
    ) -> WatchlistItemResponse:
        clean_symbol = (
            symbol.strip().upper()
        )

        if not clean_symbol:
            raise WatchlistAssetNotFoundError(
                "Symbol cannot be empty."
            )

        asset = (
            self.asset_repository
            .get_by_symbol(
                clean_symbol
            )
        )

        if asset is None:
            raise WatchlistAssetNotFoundError(
                f"Asset not found for symbol: "
                f"{clean_symbol}"
            )

        existing = (
            self.watchlist_repository
            .get_by_asset_id(
                asset.id
            )
        )

        if existing is not None:
            raise WatchlistAlreadyExistsError(
                f"Asset already exists in watchlist: "
                f"{clean_symbol}"
            )

        try:
            item = (
                self.watchlist_repository
                .create(
                    asset_id=asset.id,
                )
            )

        except IntegrityError as exc:
            raise WatchlistAlreadyExistsError(
                f"Asset already exists in watchlist: "
                f"{clean_symbol}"
            ) from exc

        return self._serialize(
            item
        )

    def list_items(
        self,
    ) -> list[WatchlistItemResponse]:
        items = (
            self.watchlist_repository
            .list_items()
        )

        return [
            self._serialize(
                item
            )
            for item in items
        ]

    def get(
        self,
        symbol: str,
    ) -> WatchlistItemResponse:
        clean_symbol = (
            symbol.strip().upper()
        )

        asset = (
            self.asset_repository
            .get_by_symbol(
                clean_symbol
            )
        )

        if asset is None:
            raise WatchlistItemNotFoundError(
                f"Watchlist item not found for symbol: "
                f"{clean_symbol}"
            )

        item = (
            self.watchlist_repository
            .get_by_asset_id(
                asset.id
            )
        )

        if item is None:
            raise WatchlistItemNotFoundError(
                f"Watchlist item not found for symbol: "
                f"{clean_symbol}"
            )

        return self._serialize(
            item
        )

    def remove(
        self,
        symbol: str,
    ) -> str:
        clean_symbol = (
            symbol.strip().upper()
        )

        asset = (
            self.asset_repository
            .get_by_symbol(
                clean_symbol
            )
        )

        if asset is None:
            raise WatchlistItemNotFoundError(
                f"Watchlist item not found for symbol: "
                f"{clean_symbol}"
            )

        item = (
            self.watchlist_repository
            .get_by_asset_id(
                asset.id
            )
        )

        if item is None:
            raise WatchlistItemNotFoundError(
                f"Watchlist item not found for symbol: "
                f"{clean_symbol}"
            )

        self.watchlist_repository.delete(
            item
        )

        return clean_symbol