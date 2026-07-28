from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.market_price_repository import MarketPriceRepository
from app.services.market_ingestion_service import MarketIngestionService
from app.services.market_query_service import MarketQueryService


router = APIRouter(
    prefix="/market",
    tags=["Market"],
)


@router.post("/collect/{symbol}")
async def collect_market_price(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    asset_repository = AssetRepository(db)
    market_price_repository = MarketPriceRepository(db)

    service = MarketIngestionService(
        asset_repository=asset_repository,
        market_price_repository=market_price_repository,
    )

    try:
        saved_price = await service.collect_and_save_latest_price(symbol)

        return {
            "message": "Market price collected successfully.",
            "id": saved_price.id,
            "asset_id": saved_price.asset_id,
            "open": saved_price.open_price,
            "high": saved_price.high_price,
            "low": saved_price.low_price,
            "close": saved_price.close_price,
            "volume": saved_price.volume,
            "timestamp": saved_price.timestamp,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/latest/{symbol}")
def get_latest_market_price(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    asset_repository = AssetRepository(db)
    market_price_repository = MarketPriceRepository(db)

    service = MarketQueryService(
        asset_repository=asset_repository,
        market_price_repository=market_price_repository,
    )

    try:
        latest_price = service.get_latest_price(symbol)

        return {
            "id": latest_price.id,
            "asset_id": latest_price.asset_id,
            "symbol": symbol.strip().upper(),
            "open": latest_price.open_price,
            "high": latest_price.high_price,
            "low": latest_price.low_price,
            "close": latest_price.close_price,
            "volume": latest_price.volume,
            "timestamp": latest_price.timestamp,
            "created_at": latest_price.created_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc