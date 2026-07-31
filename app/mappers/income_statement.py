from app.models.income_statement import IncomeStatement
from app.schemas.income_statement import IncomeStatementCreate


def map_income_statement_create_to_model(
    data: IncomeStatementCreate,
    asset_id: int,
) -> IncomeStatement:
    return IncomeStatement(
        asset_id=asset_id,
        period_end_date=data.period_end_date,
        period_type=data.period_type,
        currency=data.currency,
        total_revenue=data.total_revenue,
        cost_of_revenue=data.cost_of_revenue,
        gross_profit=data.gross_profit,
        operating_expense=data.operating_expense,
        operating_income=data.operating_income,
        net_non_operating_interest_income_expense=(
            data.net_non_operating_interest_income_expense
        ),
        pretax_income=data.pretax_income,
        tax_provision=data.tax_provision,
        net_income=data.net_income,
        diluted_average_shares=data.diluted_average_shares,
        diluted_eps=data.diluted_eps,
    )