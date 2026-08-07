from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.asset_repository import (
    AssetRepository,
)
from app.repositories.balance_sheet_repository import (
    BalanceSheetRepository,
)
from app.repositories.cash_flow_statement_repository import (
    CashFlowStatementRepository,
)
from app.repositories.income_statement_repository import (
    IncomeStatementRepository,
)
from app.repositories.market_price_repository import (
    MarketPriceRepository,
)
from app.schemas.freshness import (
    AssetFreshnessResponse,
    FreshnessComponentResponse,
)


class AssetFreshnessService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.asset_repository = AssetRepository(db)
        self.market_price_repository = (
            MarketPriceRepository(db)
        )
        self.income_statement_repository = (
            IncomeStatementRepository(db)
        )
        self.balance_sheet_repository = (
            BalanceSheetRepository(db)
        )
        self.cash_flow_statement_repository = (
            CashFlowStatementRepository(db)
        )

    @staticmethod
    def _latest_quarterly_date(
        statements: list,
    ) -> date | None:
        dates = [
            statement.period_end_date
            for statement in statements
            if statement.period_type == "quarterly"
        ]

        if not dates:
            return None

        return max(dates)

    @staticmethod
    def _financial_component(
        period_end_date: date | None,
        *,
        today: date,
    ) -> FreshnessComponentResponse:
        if period_end_date is None:
            return FreshnessComponentResponse(
                status="missing",
                stale=True,
                max_age_days=(
                    settings
                    .financial_period_max_age_days
                ),
            )

        age_days = max(
            0,
            (today - period_end_date).days,
        )
        stale = (
            age_days
            > settings.financial_period_max_age_days
        )

        return FreshnessComponentResponse(
            status=(
                "stale"
                if stale
                else "fresh"
            ),
            stale=stale,
            latest_period_end_date=(
                period_end_date
            ),
            age_days=age_days,
            max_age_days=(
                settings
                .financial_period_max_age_days
            ),
        )

    @staticmethod
    def _market_component(
        timestamp: datetime | None,
        *,
        now: datetime,
    ) -> FreshnessComponentResponse:
        if timestamp is None:
            return FreshnessComponentResponse(
                status="missing",
                stale=True,
                max_age_minutes=(
                    settings
                    .market_price_max_age_minutes
                ),
            )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        age_minutes = max(
            0,
            int(
                (
                    now
                    - timestamp.astimezone(
                        timezone.utc
                    )
                ).total_seconds()
                // 60
            ),
        )
        stale = (
            age_minutes
            > settings.market_price_max_age_minutes
        )

        return FreshnessComponentResponse(
            status=(
                "stale"
                if stale
                else "fresh"
            ),
            stale=stale,
            latest_timestamp=timestamp,
            age_minutes=age_minutes,
            max_age_minutes=(
                settings
                .market_price_max_age_minutes
            ),
        )

    def get_freshness(
        self,
        symbol: str,
        *,
        now: datetime | None = None,
    ) -> AssetFreshnessResponse:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: "
                f"{clean_symbol}"
            )

        now = now or datetime.now(
            timezone.utc
        )
        today = now.date()

        market_price = (
            self.market_price_repository
            .get_latest_by_asset_id(
                asset.id
            )
        )

        income_date = self._latest_quarterly_date(
            self.income_statement_repository
            .get_by_asset_id(
                asset.id,
                limit=20,
            )
        )
        balance_date = self._latest_quarterly_date(
            self.balance_sheet_repository
            .get_by_asset_id(
                asset.id,
                limit=20,
            )
        )
        cash_flow_date = self._latest_quarterly_date(
            self.cash_flow_statement_repository
            .get_by_asset_id(
                asset.id,
                limit=20,
            )
        )

        components = {
            "market_price": self._market_component(
                (
                    market_price.timestamp
                    if market_price is not None
                    else None
                ),
                now=now,
            ),
            "income_statements": (
                self._financial_component(
                    income_date,
                    today=today,
                )
            ),
            "balance_sheets": (
                self._financial_component(
                    balance_date,
                    today=today,
                )
            ),
            "cash_flow_statements": (
                self._financial_component(
                    cash_flow_date,
                    today=today,
                )
            ),
        }

        stale_components = [
            name
            for name, component in components.items()
            if component.stale
        ]

        return AssetFreshnessResponse(
            symbol=clean_symbol,
            status=(
                "stale"
                if stale_components
                else "fresh"
            ),
            stale_components=stale_components,
            components=components,
        )
