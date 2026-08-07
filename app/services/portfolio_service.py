from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.market_price_repository import MarketPriceRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioDetailResponse,
    PortfolioPositionResponse,
    PortfolioPositionUpsert,
    PortfolioSummaryResponse,
)


class PortfolioNotFoundError(Exception):
    pass


class PortfolioAlreadyExistsError(Exception):
    pass


class PortfolioAssetNotFoundError(Exception):
    pass


class PortfolioPositionNotFoundError(Exception):
    pass


class PortfolioService:
    def __init__(self, db: Session, *, user_id: int) -> None:
        self.user_id = user_id
        self.portfolios = PortfolioRepository(db)
        self.assets = AssetRepository(db)
        self.prices = MarketPriceRepository(db)

    def create(self, data: PortfolioCreate) -> PortfolioSummaryResponse:
        if self.portfolios.get_by_name(user_id=self.user_id, name=data.name) is not None:
            raise PortfolioAlreadyExistsError("A portfolio with this name already exists.")
        try:
            portfolio = self.portfolios.create(user_id=self.user_id, name=data.name, base_currency=data.base_currency)
        except IntegrityError as exc:
            self.portfolios.db.rollback()
            raise PortfolioAlreadyExistsError("A portfolio with this name already exists.") from exc
        return self._summary(portfolio)

    def list(self) -> list[PortfolioSummaryResponse]:
        return [self._summary(item) for item in self.portfolios.list_by_user(self.user_id)]

    def get(self, portfolio_id: int) -> PortfolioDetailResponse:
        portfolio = self._get_portfolio(portfolio_id)
        positions = [self._position_response(item) for item in portfolio.positions]
        total_cost = sum((item.cost_basis for item in positions), Decimal("0"))
        valued = [item.market_value for item in positions if item.market_value is not None]
        all_valued = len(valued) == len(positions)
        total_market = sum(valued, Decimal("0")) if all_valued else None
        total_pl = (total_market - total_cost) if total_market is not None else None
        return PortfolioDetailResponse(
            **self._summary(portfolio).model_dump(),
            position_count=len(positions),
            total_cost_basis=total_cost,
            total_market_value=total_market,
            total_unrealized_profit_loss=total_pl,
            positions=positions,
        )

    def upsert_position(self, *, portfolio_id: int, symbol: str, data: PortfolioPositionUpsert) -> PortfolioDetailResponse:
        portfolio = self._get_portfolio(portfolio_id)
        clean_symbol = symbol.strip().upper()
        asset = self.assets.get_by_symbol(clean_symbol)
        if asset is None:
            raise PortfolioAssetNotFoundError(f"Asset not found for symbol: {clean_symbol}")
        self.portfolios.upsert_position(
            portfolio=portfolio,
            asset_id=asset.id,
            quantity=data.quantity,
            average_cost=data.average_cost,
            currency=data.currency or asset.currency or portfolio.base_currency,
        )
        return self.get(portfolio_id)

    def remove_position(self, *, portfolio_id: int, symbol: str) -> str:
        portfolio = self._get_portfolio(portfolio_id)
        clean_symbol = symbol.strip().upper()
        asset = self.assets.get_by_symbol(clean_symbol)
        if asset is None:
            raise PortfolioPositionNotFoundError(f"Portfolio position not found for symbol: {clean_symbol}")
        position = self.portfolios.get_position(portfolio_id=portfolio.id, asset_id=asset.id)
        if position is None:
            raise PortfolioPositionNotFoundError(f"Portfolio position not found for symbol: {clean_symbol}")
        self.portfolios.delete_position(position)
        return clean_symbol

    def delete(self, portfolio_id: int) -> None:
        self.portfolios.delete(self._get_portfolio(portfolio_id))

    def _get_portfolio(self, portfolio_id: int):
        portfolio = self.portfolios.get_for_user(portfolio_id=portfolio_id, user_id=self.user_id)
        if portfolio is None:
            raise PortfolioNotFoundError(f"Portfolio not found: {portfolio_id}")
        return portfolio

    @staticmethod
    def _summary(portfolio) -> PortfolioSummaryResponse:
        return PortfolioSummaryResponse(
            id=portfolio.id,
            name=portfolio.name,
            base_currency=portfolio.base_currency,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    def _position_response(self, position) -> PortfolioPositionResponse:
        asset = position.asset
        latest = self.prices.get_latest_by_asset_id(asset.id)
        latest_price = Decimal(str(latest.close_price)) if latest is not None else None
        quantity = Decimal(position.quantity)
        average_cost = Decimal(position.average_cost)
        cost_basis = quantity * average_cost
        market_value = quantity * latest_price if latest_price is not None else None
        pl = market_value - cost_basis if market_value is not None else None
        pl_pct = (pl / cost_basis * Decimal("100")) if pl is not None and cost_basis != 0 else None
        return PortfolioPositionResponse(
            id=position.id,
            asset_id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            quantity=quantity,
            average_cost=average_cost,
            currency=position.currency,
            latest_price=latest_price,
            cost_basis=cost_basis,
            market_value=market_value,
            unrealized_profit_loss=pl,
            unrealized_profit_loss_percent=pl_pct,
        )
