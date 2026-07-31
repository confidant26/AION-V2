from sqlalchemy.orm import Session

from app.models.balance_sheet import BalanceSheet
from app.providers.financial.yahoo_balance_sheet_provider import (
    YahooBalanceSheetProvider,
)
from app.repositories.asset_repository import AssetRepository
from app.repositories.balance_sheet_repository import (
    BalanceSheetRepository,
)


class BalanceSheetService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.asset_repository = AssetRepository(db)
        self.balance_sheet_repository = (
            BalanceSheetRepository(db)
        )

    async def collect_balance_sheets(
        self,
        symbol: str,
    ) -> list[BalanceSheet]:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        statements = YahooBalanceSheetProvider.fetch(
            asset_id=asset.id,
            symbol=asset.symbol,
            currency=asset.currency,
        )

        if not statements:
            raise ValueError(
                f"Balance sheets not found for symbol: "
                f"{clean_symbol}"
            )

        saved_statements: list[BalanceSheet] = []

        try:
            for statement in statements:
                saved_statement = (
                    self.balance_sheet_repository.upsert(
                        statement
                    )
                )

                saved_statements.append(saved_statement)

            self.db.commit()

            for saved_statement in saved_statements:
                self.db.refresh(saved_statement)

            return saved_statements

        except Exception:
            self.db.rollback()
            raise

    def get_balance_sheets(
        self,
        symbol: str,
        limit: int = 20,
    ) -> list[BalanceSheet]:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        statements = (
            self.balance_sheet_repository.get_by_asset_id(
                asset_id=asset.id,
                limit=limit,
            )
        )

        if not statements:
            raise ValueError(
                f"Balance sheets not found for symbol: "
                f"{clean_symbol}"
            )

        return statements