from datetime import date

from sqlalchemy import BigInteger
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class IncomeStatement(Base):
    __tablename__ = "income_statements"

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "period_end_date",
            "period_type",
            name="uq_income_statements_asset_period",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"),
        nullable=False,
        index=True,
    )

    period_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    currency: Mapped[str | None] = mapped_column(
        String(20),
    )

    total_revenue: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    cost_of_revenue: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    gross_profit: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    operating_expense: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    operating_income: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    net_non_operating_interest_income_expense: Mapped[int | None] = (
        mapped_column(
            BigInteger,
        )
    )

    pretax_income: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    tax_provision: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    net_income: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    diluted_average_shares: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    diluted_eps: Mapped[str | None] = mapped_column(
        String(50),
    )

    asset = relationship("Asset")