import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

from app.models.asset import Asset
from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.company_profile import CompanyProfile
from app.models.income_statement import IncomeStatement
from app.models.market_price import MarketPrice
from app.models.portfolio import Portfolio, PortfolioPosition
from app.models.user import User
from app.models.watchlist_item import WatchlistItem


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(
        bind=engine,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()

        Base.metadata.drop_all(
            bind=engine,
        )

        engine.dispose()
