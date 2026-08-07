from __future__ import annotations

import argparse
import asyncio
import json

from app.db.session import SessionLocal
from app.repositories.asset_repository import (
    AssetRepository,
)
from app.repositories.watchlist_repository import (
    WatchlistRepository,
)
from app.services.asset_batch_refresh_service import (
    AssetBatchRefreshService,
)


def _watchlist_symbols() -> list[str]:
    db = SessionLocal()

    try:
        repository = WatchlistRepository(db)

        return [
            item.asset.symbol
            for item in repository.list_items()
            if item.asset is not None
        ]

    finally:
        db.close()


def _active_asset_symbols() -> list[str]:
    db = SessionLocal()

    try:
        repository = AssetRepository(db)
        symbols: list[str] = []
        offset = 0
        batch_size = 500

        while True:
            assets = repository.list_assets(
                offset=offset,
                limit=batch_size,
                active_only=True,
            )

            symbols.extend(
                asset.symbol
                for asset in assets
            )

            if len(assets) < batch_size:
                break

            offset += batch_size

        return symbols

    finally:
        db.close()


async def run_refresh(
    *,
    scope: str,
    include_analysis: bool,
    concurrency: int,
) -> dict:
    if scope == "watchlist":
        symbols = _watchlist_symbols()
    elif scope == "active":
        symbols = _active_asset_symbols()
    else:
        raise ValueError(
            f"Unsupported refresh scope: {scope}"
        )

    if not symbols:
        return {
            "scope": scope,
            "requested_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "results": [],
        }

    result = await AssetBatchRefreshService().refresh_many(
        symbols=symbols,
        include_analysis=include_analysis,
        concurrency=concurrency,
    )

    return {
        "scope": scope,
        **result.model_dump(
            mode="json"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh AION assets from an external scheduler "
            "such as cron or Windows Task Scheduler."
        )
    )
    parser.add_argument(
        "--scope",
        choices=(
            "watchlist",
            "active",
        ),
        default="watchlist",
    )
    parser.add_argument(
        "--include-analysis",
        action="store_true",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    result = asyncio.run(
        run_refresh(
            scope=args.scope,
            include_analysis=(
                args.include_analysis
            ),
            concurrency=args.concurrency,
        )
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
