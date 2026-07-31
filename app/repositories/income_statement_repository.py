from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.income_statement import IncomeStatement


class IncomeStatementRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        income_statement: IncomeStatement,
    ) -> IncomeStatement:
        self.db.add(income_statement)
        self.db.commit()
        self.db.refresh(income_statement)

        return income_statement

    def get_by_asset_and_period(
        self,
        asset_id: int,
        period_end_date: date,
        period_type: str,
    ) -> IncomeStatement | None:
        statement = select(IncomeStatement).where(
            IncomeStatement.asset_id == asset_id,
            IncomeStatement.period_end_date == period_end_date,
            IncomeStatement.period_type == period_type,
        )

        return self.db.scalar(statement)

    def get_by_asset_id(
        self,
        asset_id: int,
        limit: int = 20,
    ) -> list[IncomeStatement]:
        statement = (
            select(IncomeStatement)
            .where(
                IncomeStatement.asset_id == asset_id,
            )
            .order_by(
                IncomeStatement.period_end_date.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update(
        self,
        income_statement: IncomeStatement,
    ) -> IncomeStatement:
        self.db.commit()
        self.db.refresh(income_statement)

        return income_statement