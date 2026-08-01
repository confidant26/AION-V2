from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company_profile import CompanyProfile
from app.models.income_statement import IncomeStatement


class ValuationMetricsRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_company_profile(
        self,
        *,
        asset_id: int,
    ) -> CompanyProfile | None:
        statement = select(CompanyProfile).where(
            CompanyProfile.asset_id == asset_id,
        )

        return self.db.scalar(statement)

    def get_matched_periods(
        self,
        *,
        asset_id: int,
        period_type: str | None = None,
        limit: int = 20,
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
            )
        )

        if period_type is not None:
            statement = statement.where(
                IncomeStatement.period_type == period_type,
            )

        statement = statement.order_by(
            IncomeStatement.period_end_date.desc(),
            IncomeStatement.period_type.asc(),
        ).limit(limit)

        results = self.db.execute(statement).all()

        return [
            (
                row[0],
                row[1],
                row[2],
            )
            for row in results
        ]