from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    asset_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    exchange: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    market: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        index=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
    )

    sector: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    industry: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    isin: Mapped[str | None] = mapped_column(
        String(12),
        unique=True,
        nullable=True,
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    market_prices = relationship(
        "MarketPrice",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    income_statements = relationship(
        "IncomeStatement",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    balance_sheets = relationship(
        "BalanceSheet",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    cash_flow_statements = relationship(
        "CashFlowStatement",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    company_profiles = relationship(
        "CompanyProfile",
        back_populates="asset",
        cascade="all, delete-orphan",
    )


    watchlist_items = relationship(
        "WatchlistItem",
        back_populates="asset",
    )

    portfolio_positions = relationship(
        "PortfolioPosition",
        back_populates="asset",
    )
