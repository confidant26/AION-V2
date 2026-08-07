from datetime import date

from sqlalchemy.orm import Session

from app.providers.company.factory import get_company_data_provider
from app.providers.financial.factory import get_financial_data_provider
from app.repositories.asset_repository import AssetRepository
from app.repositories.market_price_repository import (
    MarketPriceRepository,
)
from app.services.balance_sheet_service import BalanceSheetService
from app.services.cash_flow_statement_service import (
    CashFlowStatementService,
)
from app.services.company_profile_service import CompanyProfileService
from app.services.composite_score_service import CompositeScoreService
from app.services.income_statement_service import IncomeStatementService
from app.services.market_ingestion_service import MarketIngestionService
from app.services.ttm_financials_service import TTMFinancialsService
from app.services.ttm_valuation_metrics_service import (
    TTMValuationMetricsService,
)
from app.providers.telemetry import get_provider_trace_summary


class AssetRefreshService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.asset_repository = AssetRepository(db)

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
    def _serialize_company_profile(
        profile,
    ) -> dict:
        return {
            "id": profile.id,
            "asset_id": profile.asset_id,
            "company_name": profile.company_name,
            "sector": profile.sector,
            "industry": profile.industry,
            "country": profile.country,
            "currency": profile.currency,
            "market_cap": profile.market_cap,
            "full_time_employees": (
                profile.full_time_employees
            ),
            "website": profile.website,
        }

    @staticmethod
    def _serialize_market_price(
        price,
    ) -> dict:
        return {
            "id": price.id,
            "asset_id": price.asset_id,
            "open": price.open_price,
            "high": price.high_price,
            "low": price.low_price,
            "close": price.close_price,
            "volume": price.volume,
            "timestamp": price.timestamp,
        }

    async def refresh(
        self,
        *,
        symbol: str,
        include_analysis: bool = False,
    ) -> dict:
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
                f"Asset not found for symbol: {clean_symbol}"
            )

        company_provider = (
            get_company_data_provider()
        )

        financial_provider = (
            get_financial_data_provider()
        )

        company_service = CompanyProfileService(
            db=self.db,
            provider=company_provider,
        )

        market_service = MarketIngestionService(
            asset_repository=self.asset_repository,
            market_price_repository=(
                MarketPriceRepository(self.db)
            ),
        )

        income_service = IncomeStatementService(
            db=self.db,
            provider=financial_provider,
        )

        balance_service = BalanceSheetService(
            db=self.db,
        )

        cash_flow_service = (
            CashFlowStatementService(
                db=self.db,
            )
        )

        company_profile = (
            await company_service.collect_company_profile(
                clean_symbol
            )
        )

        market_price = (
            await market_service.collect_and_save_latest_price(
                clean_symbol
            )
        )

        income_statements = (
            await income_service.collect_income_statements(
                clean_symbol
            )
        )

        balance_sheets = (
            await balance_service.collect_balance_sheets(
                clean_symbol
            )
        )

        cash_flow_statements = (
            await cash_flow_service.collect_cash_flow_statements(
                clean_symbol
            )
        )

        latest_income_quarter = (
            self._latest_quarterly_date(
                income_statements
            )
        )

        latest_balance_quarter = (
            self._latest_quarterly_date(
                balance_sheets
            )
        )

        latest_cash_flow_quarter = (
            self._latest_quarterly_date(
                cash_flow_statements
            )
        )

        quarterly_dates = [
            latest_income_quarter,
            latest_balance_quarter,
            latest_cash_flow_quarter,
        ]

        alignment_ok = (
            all(
                value is not None
                for value in quarterly_dates
            )
            and len(set(quarterly_dates)) == 1
        )

        available_dates = [
            value
            for value in quarterly_dates
            if value is not None
        ]

        spread_days = (
            (
                max(available_dates)
                - min(available_dates)
            ).days
            if available_dates
            else None
        )

        warnings: list[str] = []

        if not alignment_ok:
            warnings.append(
                "Latest quarterly financial periods "
                "are not aligned."
            )

        response = {
            "message": (
                "Asset refreshed successfully."
            ),
            "symbol": clean_symbol,
            "status": (
                "healthy"
                if not warnings
                else "warning"
            ),
            "warnings": warnings,
            "company_profile": (
                self._serialize_company_profile(
                    company_profile
                )
            ),
            "market_price": (
                self._serialize_market_price(
                    market_price
                )
            ),
            "financials": {
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
                    "ok": alignment_ok,
                    "spread_days": spread_days,
                },
            },
        }

        if include_analysis:
            ttm_financials = (
                TTMFinancialsService(
                    db=self.db,
                ).get_ttm_financials(
                    clean_symbol
                )
            )

            valuation_metrics = (
                TTMValuationMetricsService(
                    db=self.db,
                ).get_ttm_valuation_metrics(
                    clean_symbol
                )
            )

            composite_score = (
                CompositeScoreService(
                    db=self.db,
                ).get_composite_score(
                    clean_symbol
                )
            )

            response["analysis"] = {
                "ttm_financials": (
                    ttm_financials.model_dump(
                        mode="json"
                    )
                ),
                "ttm_valuation_metrics": (
                    valuation_metrics.model_dump(
                        mode="json"
                    )
                ),
                "composite_score": (
                    composite_score.model_dump(
                        mode="json"
                    )
                ),
            }

        response["provider_observability"] = (
            get_provider_trace_summary()
        )

        return response
