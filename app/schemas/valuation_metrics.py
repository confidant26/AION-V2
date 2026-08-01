from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ValuationMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_end_date: date
    period_type: str
    currency: str | None = None

    market_cap: Decimal | None = None
    enterprise_value: Decimal | None = None

    price_to_earnings: Decimal | None = None
    price_to_sales: Decimal | None = None
    price_to_book: Decimal | None = None
    ev_to_ebitda: Decimal | None = None
    free_cash_flow_yield: Decimal | None = None
    earnings_yield: Decimal | None = None

    company_profile_id: int
    income_statement_id: int
    balance_sheet_id: int
    cash_flow_statement_id: int

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )