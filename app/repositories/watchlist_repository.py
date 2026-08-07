from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.watchlist_item import WatchlistItem


class WatchlistRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get_by_asset_id(
        self,
        asset_id: int,
    ) -> WatchlistItem | None:
        statement = (
            select(WatchlistItem)
            .options(
                selectinload(
                    WatchlistItem.asset
                )
            )
            .where(
                WatchlistItem.asset_id
                == asset_id
            )
        )

        return self.db.scalar(
            statement
        )

    def list_items(
        self,
    ) -> list[WatchlistItem]:
        statement = (
            select(WatchlistItem)
            .options(
                selectinload(
                    WatchlistItem.asset
                )
            )
            .order_by(
                WatchlistItem.created_at.desc(),
                WatchlistItem.id.desc(),
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def create(
        self,
        *,
        asset_id: int,
    ) -> WatchlistItem:
        item = WatchlistItem(
            asset_id=asset_id,
        )

        self.db.add(
            item
        )

        try:
            self.db.commit()

        except IntegrityError:
            self.db.rollback()
            raise

        self.db.refresh(
            item
        )

        return self.get_by_asset_id(
            asset_id
        ) or item

    def delete(
        self,
        item: WatchlistItem,
    ) -> None:
        self.db.delete(
            item
        )
        self.db.commit()