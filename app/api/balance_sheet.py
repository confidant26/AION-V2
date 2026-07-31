from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.balance_sheet_service import BalanceSheetService


router = APIRouter(
    prefix="/balance-sheets",
    tags=["Balance Sheets"],
)


@router.post("/collect/{symbol}")
async def collect_balance_sheets(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    service = BalanceSheetService(db=db)

    try:
        statements = await service.collect_balance_sheets(
            symbol
        )

        return {
            "message": "Balance sheets collected successfully.",
            "symbol": symbol.strip().upper(),
            "count": len(statements),
            "statements": [
                {
                    "id": statement.id,
                    "asset_id": statement.asset_id,
                    "period_end_date": statement.period_end_date,
                    "period_type": statement.period_type,
                    "currency": statement.currency,
                    "total_assets": statement.total_assets,
                    "current_assets": statement.current_assets,
                    "cash_and_cash_equivalents": (
                        statement.cash_and_cash_equivalents
                    ),
                    "inventory": statement.inventory,
                    "total_liabilities": (
                        statement.total_liabilities
                    ),
                    "current_liabilities": (
                        statement.current_liabilities
                    ),
                    "long_term_debt": statement.long_term_debt,
                    "stockholders_equity": (
                        statement.stockholders_equity
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
def get_balance_sheets(
    symbol: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of balance sheet records to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> dict:
    service = BalanceSheetService(db=db)

    try:
        statements = service.get_balance_sheets(
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
                    "total_assets": statement.total_assets,
                    "current_assets": statement.current_assets,
                    "cash_and_cash_equivalents": (
                        statement.cash_and_cash_equivalents
                    ),
                    "inventory": statement.inventory,
                    "total_liabilities": (
                        statement.total_liabilities
                    ),
                    "current_liabilities": (
                        statement.current_liabilities
                    ),
                    "long_term_debt": statement.long_term_debt,
                    "stockholders_equity": (
                        statement.stockholders_equity
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