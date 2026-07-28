import asyncio

from app.db.session import SessionLocal
from app.repositories.asset_repository import AssetRepository
from app.repositories.market_price_repository import MarketPriceRepository
from app.services.market_ingestion_service import MarketIngestionService


async def main() -> None:
    db = SessionLocal()

    try:
        asset_repository = AssetRepository(db)
        market_price_repository = MarketPriceRepository(db)

        service = MarketIngestionService(
            asset_repository=asset_repository,
            market_price_repository=market_price_repository,
            provider_name="yahoo",
        )

        saved_price = await service.collect_and_save_latest_price("AAPL")

        print("Kayıt başarılı.")
        print("Market price id:", saved_price.id)
        print("Asset id:", saved_price.asset_id)
        print("Close price:", saved_price.close_price)
        print("Timestamp:", saved_price.timestamp)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())