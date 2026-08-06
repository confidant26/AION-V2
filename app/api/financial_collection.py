from datetime import date

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


def _latest_period_end_date(
    statements: list,
) -> date | None:
    if not statements:
        return None

    return max(
        statement.period_end_date
        for statement in statements
    )


def _latest_quarterly_period_end_date(
    statements: list,
) -> date | None:
    quarterly_dates = [
        statement.period_end_date
        for statement in statements
        if statement.period_type == "quarterly"
    ]

    if not quarterly_dates:
        return None

    return max(quarterly_dates)


def _calculate_date_spread_days(
    dates: list[date | None],
) -> int | None:
    available_dates = [
        value
        for value in dates
        if value is not None
    ]

    if not available_dates:
        return None

    return (
        max(available_dates)
        - min(available_dates)
    ).days


def _quarterly_alignment_ok(
    dates: list[date | None],
) -> bool:
    if any(
        value is None
        for value in dates
    ):
        return False

    return len(
        set(dates)
    ) == 1


def _build_data_quality_warnings(
    *,
    income_statements: list,
    balance_sheets: list,
    cash_flow_statements: list,
    latest_income_quarter: date | None,
    latest_balance_quarter: date | None,
    latest_cash_flow_quarter: date | None,
) -> list[str]:
    warnings: list[str] = []

    if not income_statements:
        warnings.append(
            "Income statements are missing."
        )

    if not balance_sheets:
        warnings.append(
            "Balance sheets are missing."
        )

    if not cash_flow_statements:
        warnings.append(
            "Cash flow statements are missing."
        )

    quarterly_dates = [
        latest_income_quarter,
        latest_balance_quarter,
        latest_cash_flow_quarter,
    ]

    if not _quarterly_alignment_ok(
        quarterly_dates
    ):
        warnings.append(
            "Latest quarterly financial periods are not aligned."
        )

    return warnings


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

    balance_sheet_service = BalanceSheetService(
        db=db,
    )

    cash_flow_service = CashFlowStatementService(
        db=db,
    )

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

        latest_income_date = (
            _latest_period_end_date(
                income_statements
            )
        )

        latest_balance_date = (
            _latest_period_end_date(
                balance_sheets
            )
        )

        latest_cash_flow_date = (
            _latest_period_end_date(
                cash_flow_statements
            )
        )

        latest_income_quarter = (
            _latest_quarterly_period_end_date(
                income_statements
            )
        )

        latest_balance_quarter = (
            _latest_quarterly_period_end_date(
                balance_sheets
            )
        )

        latest_cash_flow_quarter = (
            _latest_quarterly_period_end_date(
                cash_flow_statements
            )
        )

        quarterly_dates = [
            latest_income_quarter,
            latest_balance_quarter,
            latest_cash_flow_quarter,
        ]

        quarterly_alignment_ok = (
            _quarterly_alignment_ok(
                quarterly_dates
            )
        )

        quarterly_spread_days = (
            _calculate_date_spread_days(
                quarterly_dates
            )
        )

        warnings = (
            _build_data_quality_warnings(
                income_statements=(
                    income_statements
                ),
                balance_sheets=(
                    balance_sheets
                ),
                cash_flow_statements=(
                    cash_flow_statements
                ),
                latest_income_quarter=(
                    latest_income_quarter
                ),
                latest_balance_quarter=(
                    latest_balance_quarter
                ),
                latest_cash_flow_quarter=(
                    latest_cash_flow_quarter
                ),
            )
        )

        data_quality_status = (
            "healthy"
            if not warnings
            else "warning"
        )

        return {
            "message": (
                "Financial statements collected successfully."
            ),
            "symbol": clean_symbol,
            "counts": {
                "income_statements": len(
                    income_statements
                ),
                "balance_sheets": len(
                    balance_sheets
                ),
                "cash_flow_statements": len(
                    cash_flow_statements
                ),
            },
            "total_count": (
                len(income_statements)
                + len(balance_sheets)
                + len(cash_flow_statements)
            ),
            "latest_periods": {
                "income_statements": (
                    latest_income_date
                ),
                "balance_sheets": (
                    latest_balance_date
                ),
                "cash_flow_statements": (
                    latest_cash_flow_date
                ),
            },
            "latest_quarterly_periods": {
                "income_statements": (
                    latest_income_quarter
                ),
                "balance_sheets": (
                    latest_balance_quarter
                ),
                "cash_flow_statements": (
                    latest_cash_flow_quarter
                ),
            },
            "quarterly_alignment": {
                "ok": quarterly_alignment_ok,
                "spread_days": (
                    quarterly_spread_days
                ),
            },
            "data_quality": {
                "status": (
                    data_quality_status
                ),
                "warnings": warnings,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc