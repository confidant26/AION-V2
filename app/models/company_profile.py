from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"),
        unique=True,
        nullable=False,
    )

    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sector: Mapped[str | None] = mapped_column(
        String(255),
    )

    industry: Mapped[str | None] = mapped_column(
        String(255),
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
    )

    currency: Mapped[str | None] = mapped_column(
        String(20),
    )

    market_cap: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    full_time_employees: Mapped[int | None] = mapped_column(
        Integer,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    asset = relationship("Asset")