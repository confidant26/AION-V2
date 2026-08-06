from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.providers.financial.factory import get_financial_data_provider
from app.services.balance_sheet_service import BalanceSheetService
from app.services.cash_flow_statement_service import (
    CashFlowStatementService,
)
from app.services.income_statement_service import IncomeStatementService


router = APIRouter(
    prefix="/financials",
    tags=["Financial Collection"],
)


@router.post("/collect/{symbol}")
async def collect_financials(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    clean_symbol = symbol.strip().upper()

    provider = get_financial_data_provider()

    income_service = IncomeStatementService(
        db=db,
        provider=provider,
    )
    balance_sheet_service = BalanceSheetService(db=db)
    cash_flow_service = CashFlowStatementService(db=db)

    try:
        income_statements = (
            await income_service.collect_income_statements(
                clean_symbol
            )
        )

        balance_sheets = (
            await balance_sheet_service.collect_balance_sheets(
                clean_symbol
            )
        )

        cash_flow_statements = (
            await cash_flow_service.collect_cash_flow_statements(
                clean_symbol
            )
        )

        return {
            "message": "Financial statements collected successfully.",
            "symbol": clean_symbol,
            "counts": {
                "income_statements": len(income_statements),
                "balance_sheets": len(balance_sheets),
                "cash_flow_statements": len(cash_flow_statements),
            },
            "total_count": (
                len(income_statements)
                + len(balance_sheets)
                + len(cash_flow_statements)
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
