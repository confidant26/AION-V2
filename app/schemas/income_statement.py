from datetime import date

from pydantic import BaseModel


class IncomeStatementCreate(BaseModel):
    period_end_date: date
    period_type: str

    currency: str | None = None

    total_revenue: int | None = None
    cost_of_revenue: int | None = None
    gross_profit: int | None = None

    operating_expense: int | None = None
    operating_income: int | None = None

    net_non_operating_interest_income_expense: int | None = None

    pretax_income: int | None = None
    tax_provision: int | None = None
    net_income: int | None = None

    diluted_average_shares: int | None = None
    diluted_eps: str | None = None


class IncomeStatementResponse(IncomeStatementCreate):
    id: int
    asset_id: int

    model_config = {
        "from_attributes": True,
    }