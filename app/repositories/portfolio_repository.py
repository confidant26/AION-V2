from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.portfolio import Portfolio, PortfolioPosition


class PortfolioRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: int, name: str, base_currency: str) -> Portfolio:
        portfolio = Portfolio(user_id=user_id, name=name, base_currency=base_currency)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def list_by_user(self, user_id: int) -> list[Portfolio]:
        stmt = select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at.asc(), Portfolio.id.asc())
        return list(self.db.scalars(stmt).all())

    def get_for_user(self, *, portfolio_id: int, user_id: int) -> Portfolio | None:
        stmt = (
            select(Portfolio)
            .options(selectinload(Portfolio.positions).selectinload(PortfolioPosition.asset))
            .where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        )
        return self.db.scalar(stmt)

    def get_by_name(self, *, user_id: int, name: str) -> Portfolio | None:
        return self.db.scalar(select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.name == name))

    def upsert_position(self, *, portfolio: Portfolio, asset_id: int, quantity, average_cost, currency: str | None) -> PortfolioPosition:
        existing = self.db.scalar(
            select(PortfolioPosition).where(
                PortfolioPosition.portfolio_id == portfolio.id,
                PortfolioPosition.asset_id == asset_id,
            )
        )
        if existing is None:
            existing = PortfolioPosition(
                portfolio_id=portfolio.id,
                asset_id=asset_id,
                quantity=quantity,
                average_cost=average_cost,
                currency=currency,
            )
            self.db.add(existing)
        else:
            existing.quantity = quantity
            existing.average_cost = average_cost
            existing.currency = currency
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete_position(self, position: PortfolioPosition) -> None:
        self.db.delete(position)
        self.db.commit()

    def get_position(self, *, portfolio_id: int, asset_id: int) -> PortfolioPosition | None:
        return self.db.scalar(
            select(PortfolioPosition).where(
                PortfolioPosition.portfolio_id == portfolio_id,
                PortfolioPosition.asset_id == asset_id,
            )
        )

    def delete(self, portfolio: Portfolio) -> None:
        self.db.delete(portfolio)
        self.db.commit()
