from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.cash_flow_statement_service import (
    CashFlowStatementService,
)


router = APIRouter(
    prefix="/cash-flow-statements",
    tags=["Cash Flow Statements"],
)


@router.post("/collect/{symbol}")
async def collect_cash_flow_statements(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    service = CashFlowStatementService(db=db)

    try:
        statements = await service.collect_cash_flow_statements(
            symbol
        )

        return {
            "message": (
                "Cash flow statements collected successfully."
            ),
            "symbol": symbol.strip().upper(),
            "count": len(statements),
            "statements": [
                {
                    "id": statement.id,
                    "asset_id": statement.asset_id,
                    "period_end_date": statement.period_end_date,
                    "period_type": statement.period_type,
                    "currency": statement.currency,
                    "operating_cash_flow": (
                        statement.operating_cash_flow
                    ),
                    "investing_cash_flow": (
                        statement.investing_cash_flow
                    ),
                    "financing_cash_flow": (
                        statement.financing_cash_flow
                    ),
                    "capital_expenditure": (
                        statement.capital_expenditure
                    ),
                    "free_cash_flow": statement.free_cash_flow,
                    "depreciation_and_amortization": (
                        statement.depreciation_and_amortization
                    ),
                    "stock_based_compensation": (
                        statement.stock_based_compensation
                    ),
                    "change_in_working_capital": (
                        statement.change_in_working_capital
                    ),
                    "dividends_paid": statement.dividends_paid,
                    "share_repurchases": (
                        statement.share_repurchases
                    ),
                    "debt_issuance": statement.debt_issuance,
                    "debt_repayment": statement.debt_repayment,
                    "net_change_in_cash": (
                        statement.net_change_in_cash
                    ),
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
def get_cash_flow_statements(
    symbol: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of cash flow statement "
            "records to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> dict:
    service = CashFlowStatementService(db=db)

    try:
        statements = service.get_cash_flow_statements(
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
                    "operating_cash_flow": (
                        statement.operating_cash_flow
                    ),
                    "investing_cash_flow": (
                        statement.investing_cash_flow
                    ),
                    "financing_cash_flow": (
                        statement.financing_cash_flow
                    ),
                    "capital_expenditure": (
                        statement.capital_expenditure
                    ),
                    "free_cash_flow": statement.free_cash_flow,
                    "depreciation_and_amortization": (
                        statement.depreciation_and_amortization
                    ),
                    "stock_based_compensation": (
                        statement.stock_based_compensation
                    ),
                    "change_in_working_capital": (
                        statement.change_in_working_capital
                    ),
                    "dividends_paid": statement.dividends_paid,
                    "share_repurchases": (
                        statement.share_repurchases
                    ),
                    "debt_issuance": statement.debt_issuance,
                    "debt_repayment": statement.debt_repayment,
                    "net_change_in_cash": (
                        statement.net_change_in_cash
                    ),
                }
                for statement in statements
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc