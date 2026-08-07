from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.watchlist_item import WatchlistItem


class WatchlistRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_asset_id(self, *, user_id: int, asset_id: int) -> WatchlistItem | None:
        statement = (
            select(WatchlistItem)
            .options(selectinload(WatchlistItem.asset))
            .where(WatchlistItem.user_id == user_id, WatchlistItem.asset_id == asset_id)
        )
        return self.db.scalar(statement)

    def list_items(self, *, user_id: int) -> list[WatchlistItem]:
        statement = (
            select(WatchlistItem)
            .options(selectinload(WatchlistItem.asset))
            .where(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.created_at.desc(), WatchlistItem.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def create(self, *, user_id: int, asset_id: int) -> WatchlistItem:
        item = WatchlistItem(user_id=user_id, asset_id=asset_id)
        self.db.add(item)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(item)
        return self.get_by_asset_id(user_id=user_id, asset_id=asset_id) or item

    def delete(self, item: WatchlistItem) -> None:
        self.db.delete(item)
        self.db.commit()
