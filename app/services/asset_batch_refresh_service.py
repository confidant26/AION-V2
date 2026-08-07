import asyncio
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.asset_batch_refresh import (
    AssetBatchRefreshItem,
    AssetBatchRefreshResponse,
)
from app.services.asset_refresh_service import (
    AssetRefreshService,
)


class AssetBatchRefreshService:
    def __init__(
        self,
        session_factory: Callable[
            [],
            Session,
        ] = SessionLocal,
    ) -> None:
        self.session_factory = (
            session_factory
        )

    async def _refresh_one(
        self,
        *,
        symbol: str,
        include_analysis: bool,
        semaphore: asyncio.Semaphore,
    ) -> AssetBatchRefreshItem:
        async with semaphore:
            db = self.session_factory()

            try:
                service = (
                    AssetRefreshService(
                        db=db,
                    )
                )

                result = await service.refresh(
                    symbol=symbol,
                    include_analysis=(
                        include_analysis
                    ),
                )

                return AssetBatchRefreshItem(
                    symbol=symbol,
                    success=True,
                    result=result,
                    error=None,
                )

            except Exception as exc:
                return AssetBatchRefreshItem(
                    symbol=symbol,
                    success=False,
                    result=None,
                    error=str(exc),
                )

            finally:
                db.close()

    async def refresh_many(
        self,
        *,
        symbols: list[str],
        include_analysis: bool = False,
        concurrency: int = 3,
    ) -> AssetBatchRefreshResponse:
        clean_symbols: list[str] = []
        seen: set[str] = set()

        for value in symbols:
            symbol = value.strip().upper()

            if not symbol:
                continue

            if symbol in seen:
                continue

            seen.add(symbol)
            clean_symbols.append(
                symbol
            )

        if not clean_symbols:
            raise ValueError(
                "At least one valid symbol is required."
            )

        if concurrency < 1:
            raise ValueError(
                "Concurrency must be at least one."
            )

        if concurrency > 10:
            raise ValueError(
                "Concurrency cannot be greater than 10."
            )

        semaphore = asyncio.Semaphore(
            concurrency
        )

        tasks = [
            self._refresh_one(
                symbol=symbol,
                include_analysis=(
                    include_analysis
                ),
                semaphore=semaphore,
            )
            for symbol in clean_symbols
        ]

        results = list(
            await asyncio.gather(
                *tasks
            )
        )

        success_count = sum(
            1
            for item in results
            if item.success
        )

        failed_count = (
            len(results)
            - success_count
        )

        return AssetBatchRefreshResponse(
            requested_count=len(
                clean_symbols
            ),
            success_count=(
                success_count
            ),
            failed_count=(
                failed_count
            ),
            results=results,
        )