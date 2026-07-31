from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.providers.financial.factory import get_financial_data_provider
from app.services.income_statement_service import IncomeStatementService


router = APIRouter(
    prefix="/income-statements",
    tags=["Income Statements"],
)


@router.post("/collect/{symbol}")
async def collect_income_statements(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    provider = get_financial_data_provider()

    service = IncomeStatementService(
        db=db,
        provider=provider,
    )

    try:
        statements = await service.collect_income_statements(
            symbol
        )

        return {
            "message": "Income statements collected successfully.",
            "symbol": symbol.strip().upper(),
            "count": len(statements),
            "statements": [
                {
                    "id": statement.id,
                    "asset_id": statement.asset_id,
                    "period_end_date": statement.period_end_date,
                    "period_type": statement.period_type,
                    "currency": statement.currency,
                    "total_revenue": statement.total_revenue,
                    "cost_of_revenue": statement.cost_of_revenue,
                    "gross_profit": statement.gross_profit,
                    "operating_expense": statement.operating_expense,
                    "operating_income": statement.operating_income,
                    "net_non_operating_interest_income_expense": (
                        statement
                        .net_non_operating_interest_income_expense
                    ),
                    "pretax_income": statement.pretax_income,
                    "tax_provision": statement.tax_provision,
                    "net_income": statement.net_income,
                    "diluted_average_shares": (
                        statement.diluted_average_shares
                    ),
                    "diluted_eps": statement.diluted_eps,
                }
                for statement in statements
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{symbol}")
def get_income_statements(
    symbol: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of income statement records to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> dict:
    provider = get_financial_data_provider()

    service = IncomeStatementService(
        db=db,
        provider=provider,
    )

    try:
        statements = service.get_income_statements(
            symbol=symbol,
            limit=limit,
        )

        return {
            "symbol": symbol.strip().upper(),
            "count": len(statements),
            "limit": limit,
            "statements": [
                {
                    "id": statement.id,
                    "asset_id": statement.asset_id,
                    "period_end_date": statement.period_end_date,
                    "period_type": statement.period_type,
                    "currency": statement.currency,
                    "total_revenue": statement.total_revenue,
                    "cost_of_revenue": statement.cost_of_revenue,
                    "gross_profit": statement.gross_profit,
                    "operating_expense": statement.operating_expense,
                    "operating_income": statement.operating_income,
                    "net_non_operating_interest_income_expense": (
                        statement
                        .net_non_operating_interest_income_expense
                    ),
                    "pretax_income": statement.pretax_income,
                    "tax_provision": statement.tax_provision,
                    "net_income": statement.net_income,
                    "diluted_average_shares": (
                        statement.diluted_average_shares
                    ),
                    "diluted_eps": statement.diluted_eps,
                }
                for statement in statements
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc