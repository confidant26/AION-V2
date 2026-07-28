import asyncio

from app.services.market_data_service import MarketDataService


async def main() -> None:
    service = MarketDataService("yahoo")

    price_data = await service.get_latest_price("AAPL")

    print("Provider:", service.provider.provider_name)
    print("Market data:")
    print(price_data)


if __name__ == "__main__":
    asyncio.run(main())