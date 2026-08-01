from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.income_statement import IncomeStatement


class TTMFinancialsRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_latest_matched_quarters(
        self,
        *,
        asset_id: int,
        limit: int = 4,
    ) -> list[
        tuple[
            IncomeStatement,
            BalanceSheet,
            CashFlowStatement,
        ]
    ]:
        statement = (
            select(
                IncomeStatement,
                BalanceSheet,
                CashFlowStatement,
            )
            .join(
                BalanceSheet,
                (
                    BalanceSheet.asset_id
                    == IncomeStatement.asset_id
                )
                & (
                    BalanceSheet.period_end_date
                    == IncomeStatement.period_end_date
                )
                & (
                    BalanceSheet.period_type
                    == IncomeStatement.period_type
                ),
            )
            .join(
                CashFlowStatement,
                (
                    CashFlowStatement.asset_id
                    == IncomeStatement.asset_id
                )
                & (
                    CashFlowStatement.period_end_date
                    == IncomeStatement.period_end_date
                )
                & (
                    CashFlowStatement.period_type
                    == IncomeStatement.period_type
                ),
            )
            .where(
                IncomeStatement.asset_id == asset_id,
                IncomeStatement.period_type == "quarterly",
            )
            .order_by(
                IncomeStatement.period_end_date.desc(),
            )
            .limit(limit)
        )

        results = self.db.execute(statement).all()

        return [
            (
                row[0],
                row[1],
                row[2],
            )
            for row in results
        ]