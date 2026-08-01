from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TTMFinancialsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_end_date: date
    currency: str | None = None

    total_revenue: Decimal | None = None
    operating_income: Decimal | None = None
    net_income: Decimal | None = None
    operating_cash_flow: Decimal | None = None
    capital_expenditure: Decimal | None = None
    free_cash_flow: Decimal | None = None
    depreciation_and_amortization: Decimal | None = None
    ebitda: Decimal | None = None

    cash_and_cash_equivalents: Decimal | None = None
    total_debt: Decimal | None = None
    stockholders_equity: Decimal | None = None

    quarter_end_dates: list[date] = Field(
        default_factory=list,
    )

    income_statement_ids: list[int] = Field(
        default_factory=list,
    )

    cash_flow_statement_ids: list[int] = Field(
        default_factory=list,
    )

    balance_sheet_id: int | None = None

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )