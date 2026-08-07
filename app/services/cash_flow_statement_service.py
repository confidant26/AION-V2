from sqlalchemy.orm import Session

from app.models.cash_flow_statement import CashFlowStatement
from app.providers.financial.yahoo_cash_flow_provider import (
    YahooCashFlowProvider,
)
from app.providers.resilience import run_sync_with_retry
from app.repositories.asset_repository import AssetRepository
from app.repositories.cash_flow_statement_repository import (
    CashFlowStatementRepository,
)


class CashFlowStatementService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.asset_repository = (
            AssetRepository(db)
        )

        self.cash_flow_statement_repository = (
            CashFlowStatementRepository(
                db
            )
        )

    async def collect_cash_flow_statements(
        self,
        symbol: str,
    ) -> list[CashFlowStatement]:
        clean_symbol = (
            symbol.strip().upper()
        )

        asset = (
            self.asset_repository
            .get_by_symbol(
                clean_symbol
            )
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: "
                f"{clean_symbol}"
            )

        statements = (
            await run_sync_with_retry(
                lambda: (
                    YahooCashFlowProvider
                    .fetch(
                        asset_id=asset.id,
                        symbol=asset.symbol,
                        currency=asset.currency,
                    )
                ),
                provider_name="Yahoo Finance",
                operation_name=(
                    f"cash flow statements for "
                    f"{clean_symbol}"
                ),
            )
        )

        if not statements:
            raise ValueError(
                f"Cash flow statements not found for symbol: "
                f"{clean_symbol}"
            )

        saved_statements: list[
            CashFlowStatement
        ] = []

        try:
            for statement in statements:
                saved_statement = (
                    self.cash_flow_statement_repository
                    .upsert(
                        statement
                    )
                )

                saved_statements.append(
                    saved_statement
                )

            self.db.commit()

            for saved_statement in (
                saved_statements
            ):
                self.db.refresh(
                    saved_statement
                )

            return saved_statements

        except Exception:
            self.db.rollback()
            raise

    def get_cash_flow_statements(
        self,
        symbol: str,
        limit: int = 20,
    ) -> list[CashFlowStatement]:
        clean_symbol = (
            symbol.strip().upper()
        )

        asset = (
            self.asset_repository
            .get_by_symbol(
                clean_symbol
            )
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: "
                f"{clean_symbol}"
            )

        statements = (
            self.cash_flow_statement_repository
            .get_by_asset_id(
                asset_id=asset.id,
                limit=limit,
            )
        )

        if not statements:
            raise ValueError(
                f"Cash flow statements not found for symbol: "
                f"{clean_symbol}"
            )

        return statements