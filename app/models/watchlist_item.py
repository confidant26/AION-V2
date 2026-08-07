from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            name="uq_watchlist_items_asset_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    asset = relationship(
        "Asset",
    )