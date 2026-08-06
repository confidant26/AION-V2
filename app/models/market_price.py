from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"),
        nullable=False,
        index=True,
    )

    open_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    high_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    low_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    close_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    volume: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )

    asset = relationship(
        "Asset",
        back_populates="market_prices",
    )