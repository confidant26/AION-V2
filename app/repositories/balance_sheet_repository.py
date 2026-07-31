from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.schemas.balance_sheet import BalanceSheetCreate


class BalanceSheetRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_by_asset_id(
        self,
        asset_id: int,
        limit: int = 20,
    ) -> list[BalanceSheet]:
        statement = (
            select(BalanceSheet)
            .where(
                BalanceSheet.asset_id == asset_id,
            )
            .order_by(
                BalanceSheet.period_end_date.desc(),
                BalanceSheet.period_type.asc(),
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
    ) -> BalanceSheet | None:
        statement = select(BalanceSheet).where(
            BalanceSheet.asset_id == asset_id,
            BalanceSheet.period_end_date == period_end_date,
            BalanceSheet.period_type == period_type,
        )

        return self.db.scalar(statement)

    def upsert(
        self,
        data: BalanceSheetCreate,
    ) -> BalanceSheet:
        existing = self.get_by_period(
            asset_id=data.asset_id,
            period_end_date=data.period_end_date,
            period_type=data.period_type,
        )

        payload = data.model_dump()

        if existing is None:
            balance_sheet = BalanceSheet(**payload)

            self.db.add(balance_sheet)
            self.db.flush()
            self.db.refresh(balance_sheet)

            return balance_sheet

        for field_name, value in payload.items():
            setattr(
                existing,
                field_name,
                value,
            )

        self.db.flush()
        self.db.refresh(existing)

        return existing