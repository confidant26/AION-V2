from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ValuationScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_end_date: date
    period_type: str = "ttm"
    currency: str | None = None

    earnings_yield_score: Decimal | None = None
    free_cash_flow_yield_score: Decimal | None = None
    valuation_score: Decimal | None = None

    market_cap: Decimal | None = None
    enterprise_value: Decimal | None = None

    price_to_earnings: Decimal | None = None
    price_to_sales: Decimal | None = None
    price_to_book: Decimal | None = None
    ev_to_ebitda: Decimal | None = None
    free_cash_flow_yield: Decimal | None = None
    earnings_yield: Decimal | None = None

    company_profile_id: int

    income_statement_ids: list[int] = Field(
        default_factory=list,
    )

    balance_sheet_id: int

    cash_flow_statement_ids: list[int] = Field(
        default_factory=list,
    )

    quarter_end_dates: list[date] = Field(
        default_factory=list,
    )

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )