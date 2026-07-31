from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BalanceSheet(Base):
    __tablename__ = "balance_sheets"

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "period_end_date",
            "period_type",
            name="uq_balance_sheets_asset_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    period_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    total_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    current_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    cash_and_cash_equivalents: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    inventory: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    accounts_receivable: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    total_non_current_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    property_plant_equipment: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    goodwill: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    intangible_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    total_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    current_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    accounts_payable: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    short_term_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    total_non_current_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    long_term_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    total_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    stockholders_equity: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    retained_earnings: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    asset = relationship(
        "Asset",
        back_populates="balance_sheets",
    )