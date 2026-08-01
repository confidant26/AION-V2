from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cash_flow_statement import CashFlowStatement
from app.schemas.cash_flow_statement import CashFlowStatementCreate


class CashFlowStatementRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_by_asset_id(
        self,
        asset_id: int,
        limit: int = 20,
    ) -> list[CashFlowStatement]:
        statement = (
            select(CashFlowStatement)
            .where(
                CashFlowStatement.asset_id == asset_id,
            )
            .order_by(
                CashFlowStatement.period_end_date.desc(),
                CashFlowStatement.period_type.asc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_period(
        self,
        *,
        asset_id: int,
        period_end_date: date,
        period_type: str,
    ) -> CashFlowStatement | None:
        statement = select(CashFlowStatement).where(
            CashFlowStatement.asset_id == asset_id,
            CashFlowStatement.period_end_date == period_end_date,
            CashFlowStatement.period_type == period_type,
        )

        return self.db.scalar(statement)

    def upsert(
        self,
        data: CashFlowStatementCreate,
    ) -> CashFlowStatement:
        existing = self.get_by_period(
            asset_id=data.asset_id,
            period_end_date=data.period_end_date,
            period_type=data.period_type,
        )

        payload = data.model_dump()

        if existing is None:
            cash_flow_statement = CashFlowStatement(**payload)

            self.db.add(cash_flow_statement)
            self.db.flush()
            self.db.refresh(cash_flow_statement)

            return cash_flow_statement

        for field_name, value in payload.items():
            setattr(
                existing,
                field_name,
                value,
            )

        self.db.flush()
        self.db.refresh(existing)

        return existing