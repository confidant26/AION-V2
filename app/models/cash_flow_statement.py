from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CashFlowStatement(Base):
    __tablename__ = "cash_flow_statements"

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "period_end_date",
            "period_type",
            name="uq_cash_flow_statements_asset_period",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

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

    operating_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    investing_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    financing_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    capital_expenditure: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    free_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    depreciation_and_amortization: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    stock_based_compensation: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    change_in_working_capital: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    dividends_paid: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    share_repurchases: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    debt_issuance: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    debt_repayment: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    net_change_in_cash: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 4),
        nullable=True,
    )

    asset = relationship(
        "Asset",
        back_populates="cash_flow_statements",
    )