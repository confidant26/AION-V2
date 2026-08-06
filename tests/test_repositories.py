from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models.balance_sheet import BalanceSheet
from app.models.cash_flow_statement import CashFlowStatement
from app.models.income_statement import IncomeStatement
from app.models.market_price import MarketPrice
from app.repositories.asset_repository import AssetRepository
from app.repositories.balance_sheet_repository import (
    BalanceSheetRepository,
)
from app.repositories.cash_flow_statement_repository import (
    CashFlowStatementRepository,
)
from app.repositories.financial_metrics_repository import (
    FinancialMetricsRepository,
)
from app.repositories.income_statement_repository import (
    IncomeStatementRepository,
)
from app.repositories.market_price_repository import (
    MarketPriceRepository,
)
from app.schemas.asset import AssetCreate


class FakeStatementCreate:
    def __init__(self, **values):
        for key, value in values.items():
            setattr(self, key, value)

        self._values = values

    def model_dump(self):
        return dict(self._values)


def make_asset_create(
    *,
    symbol="AAPL",
    name="Apple Inc.",
    active=True,
):
    return AssetCreate(
        symbol=symbol,
        name=name,
        asset_type="stock",
        exchange="NASDAQ",
        market="US",
        currency="USD",
        country="US",
        sector="Technology",
        industry="Consumer Electronics",
        isin=None,
        active=active,
    )


def create_asset(
    db_session,
    *,
    symbol="AAPL",
    name="Apple Inc.",
    active=True,
):
    repository = AssetRepository(db_session)

    return repository.create(
        make_asset_create(
            symbol=symbol,
            name=name,
            active=active,
        )
    )


def make_income_statement(
    *,
    asset_id,
    period_end_date,
    period_type="annual",
    total_revenue=1000,
):
    return IncomeStatement(
        asset_id=asset_id,
        period_end_date=period_end_date,
        period_type=period_type,
        currency="USD",
        total_revenue=total_revenue,
        operating_income=250,
        net_income=200,
        diluted_eps="3.25",
    )


def make_balance_sheet_data(
    *,
    asset_id,
    period_end_date,
    period_type="annual",
    total_assets=Decimal("2000"),
):
    return FakeStatementCreate(
        asset_id=asset_id,
        period_end_date=period_end_date,
        period_type=period_type,
        currency="USD",
        total_assets=total_assets,
        current_assets=Decimal("600"),
        cash_and_cash_equivalents=Decimal("300"),
        inventory=Decimal("50"),
        accounts_receivable=Decimal("100"),
        total_non_current_assets=Decimal("1400"),
        property_plant_equipment=Decimal("500"),
        goodwill=Decimal("100"),
        intangible_assets=Decimal("50"),
        total_liabilities=Decimal("1200"),
        current_liabilities=Decimal("300"),
        accounts_payable=Decimal("100"),
        short_term_debt=Decimal("50"),
        total_non_current_liabilities=Decimal("900"),
        long_term_debt=Decimal("350"),
        total_debt=Decimal("400"),
        stockholders_equity=Decimal("800"),
        retained_earnings=Decimal("500"),
    )


def make_cash_flow_data(
    *,
    asset_id,
    period_end_date,
    period_type="annual",
    free_cash_flow=Decimal("150"),
):
    return FakeStatementCreate(
        asset_id=asset_id,
        period_end_date=period_end_date,
        period_type=period_type,
        currency="USD",
        operating_cash_flow=Decimal("250"),
        investing_cash_flow=Decimal("-80"),
        financing_cash_flow=Decimal("-30"),
        capital_expenditure=Decimal("-100"),
        free_cash_flow=free_cash_flow,
        depreciation_and_amortization=Decimal("40"),
        stock_based_compensation=Decimal("20"),
        change_in_working_capital=Decimal("-10"),
        dividends_paid=Decimal("-25"),
        share_repurchases=Decimal("-30"),
        debt_issuance=Decimal("50"),
        debt_repayment=Decimal("-40"),
        net_change_in_cash=Decimal("140"),
    )


def test_asset_repository_create_and_get_by_id(
    db_session,
):
    repository = AssetRepository(db_session)

    created = repository.create(
        make_asset_create()
    )

    found = repository.get_by_id(
        created.id
    )

    assert found is not None
    assert found.id == created.id
    assert found.symbol == "AAPL"
    assert found.name == "Apple Inc."
    assert found.asset_type == "stock"
    assert found.active is True


def test_asset_repository_get_by_symbol(
    db_session,
):
    create_asset(
        db_session,
        symbol="AAPL",
    )

    repository = AssetRepository(db_session)

    found = repository.get_by_symbol(
        "AAPL"
    )

    assert found is not None
    assert found.symbol == "AAPL"


def test_asset_repository_returns_none_for_missing_asset(
    db_session,
):
    repository = AssetRepository(db_session)

    assert repository.get_by_id(999) is None
    assert repository.get_by_symbol("INVALID") is None


def test_asset_repository_lists_assets_in_symbol_order(
    db_session,
):
    create_asset(
        db_session,
        symbol="MSFT",
        name="Microsoft",
    )
    create_asset(
        db_session,
        symbol="AAPL",
        name="Apple",
    )
    create_asset(
        db_session,
        symbol="GOOG",
        name="Alphabet",
    )

    repository = AssetRepository(db_session)

    result = repository.list_assets(
        offset=0,
        limit=10,
        active_only=False,
    )

    assert [
        asset.symbol
        for asset in result
    ] == [
        "AAPL",
        "GOOG",
        "MSFT",
    ]


def test_asset_repository_active_only_filter(
    db_session,
):
    create_asset(
        db_session,
        symbol="AAPL",
        active=True,
    )
    create_asset(
        db_session,
        symbol="MSFT",
        active=False,
    )

    repository = AssetRepository(db_session)

    result = repository.list_assets(
        active_only=True,
    )

    assert [
        asset.symbol
        for asset in result
    ] == ["AAPL"]


def test_asset_repository_offset_and_limit(
    db_session,
):
    for symbol in [
        "AAPL",
        "GOOG",
        "MSFT",
    ]:
        create_asset(
            db_session,
            symbol=symbol,
            name=symbol,
        )

    repository = AssetRepository(db_session)

    result = repository.list_assets(
        offset=1,
        limit=1,
        active_only=False,
    )

    assert len(result) == 1
    assert result[0].symbol == "GOOG"


def test_market_price_repository_returns_latest_price(
    db_session,
):
    asset = create_asset(db_session)

    now = datetime.now(timezone.utc)

    older = MarketPrice(
        asset_id=asset.id,
        open_price=100.0,
        high_price=110.0,
        low_price=95.0,
        close_price=105.0,
        volume=1000,
        timestamp=now - timedelta(days=1),
    )

    newer = MarketPrice(
        asset_id=asset.id,
        open_price=200.0,
        high_price=210.0,
        low_price=195.0,
        close_price=205.0,
        volume=2000,
        timestamp=now,
    )

    db_session.add_all(
        [
            older,
            newer,
        ]
    )
    db_session.commit()

    repository = MarketPriceRepository(
        db_session
    )

    result = (
        repository
        .get_latest_by_asset_id(
            asset.id
        )
    )

    assert result is not None
    assert result.id == newer.id
    assert result.close_price == 205.0


def test_market_price_repository_history_is_newest_first(
    db_session,
):
    asset = create_asset(db_session)

    base_time = datetime.now(
        timezone.utc
    )

    prices = []

    for index in range(3):
        price = MarketPrice(
            asset_id=asset.id,
            close_price=100.0 + index,
            timestamp=(
                base_time
                + timedelta(
                    minutes=index
                )
            ),
        )
        prices.append(price)

    db_session.add_all(prices)
    db_session.commit()

    repository = MarketPriceRepository(
        db_session
    )

    result = repository.list_by_asset_id(
        asset_id=asset.id,
        limit=2,
    )

    assert len(result) == 2
    assert [
        item.close_price
        for item in result
    ] == [
        102.0,
        101.0,
    ]


def test_income_statement_repository_create_and_find_period(
    db_session,
):
    asset = create_asset(db_session)

    repository = IncomeStatementRepository(
        db_session
    )

    period = date(
        2025,
        9,
        30,
    )

    created = repository.create(
        make_income_statement(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    found = (
        repository
        .get_by_asset_and_period(
            asset_id=asset.id,
            period_end_date=period,
            period_type="annual",
        )
    )

    assert found is not None
    assert found.id == created.id
    assert found.total_revenue == 1000


def test_income_statement_repository_lists_newest_first(
    db_session,
):
    asset = create_asset(db_session)

    repository = IncomeStatementRepository(
        db_session
    )

    repository.create(
        make_income_statement(
            asset_id=asset.id,
            period_end_date=date(
                2024,
                9,
                30,
            ),
        )
    )

    repository.create(
        make_income_statement(
            asset_id=asset.id,
            period_end_date=date(
                2025,
                9,
                30,
            ),
        )
    )

    result = repository.get_by_asset_id(
        asset_id=asset.id,
        limit=10,
    )

    assert [
        item.period_end_date
        for item in result
    ] == [
        date(2025, 9, 30),
        date(2024, 9, 30),
    ]


def test_income_statement_repository_update(
    db_session,
):
    asset = create_asset(db_session)

    repository = IncomeStatementRepository(
        db_session
    )

    statement = repository.create(
        make_income_statement(
            asset_id=asset.id,
            period_end_date=date(
                2025,
                9,
                30,
            ),
        )
    )

    statement.total_revenue = 2500

    updated = repository.update(
        statement
    )

    assert updated.total_revenue == 2500

    db_session.expire_all()

    found = (
        repository
        .get_by_asset_and_period(
            asset_id=asset.id,
            period_end_date=date(
                2025,
                9,
                30,
            ),
            period_type="annual",
        )
    )

    assert found is not None
    assert found.total_revenue == 2500


def test_balance_sheet_repository_inserts_new_period(
    db_session,
):
    asset = create_asset(db_session)

    repository = BalanceSheetRepository(
        db_session
    )

    period = date(
        2025,
        9,
        30,
    )

    saved = repository.upsert(
        make_balance_sheet_data(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    db_session.commit()

    found = repository.get_by_period(
        asset_id=asset.id,
        period_end_date=period,
        period_type="annual",
    )

    assert found is not None
    assert found.id == saved.id
    assert (
        found.total_assets
        == Decimal("2000")
    )


def test_balance_sheet_repository_updates_existing_period(
    db_session,
):
    asset = create_asset(db_session)

    repository = BalanceSheetRepository(
        db_session
    )

    period = date(
        2025,
        9,
        30,
    )

    first = repository.upsert(
        make_balance_sheet_data(
            asset_id=asset.id,
            period_end_date=period,
            total_assets=Decimal(
                "2000"
            ),
        )
    )
    db_session.commit()

    second = repository.upsert(
        make_balance_sheet_data(
            asset_id=asset.id,
            period_end_date=period,
            total_assets=Decimal(
                "3000"
            ),
        )
    )
    db_session.commit()

    assert second.id == first.id
    assert (
        second.total_assets
        == Decimal("3000")
    )


def test_cash_flow_repository_inserts_and_updates_period(
    db_session,
):
    asset = create_asset(db_session)

    repository = (
        CashFlowStatementRepository(
            db_session
        )
    )

    period = date(
        2025,
        9,
        30,
    )

    first = repository.upsert(
        make_cash_flow_data(
            asset_id=asset.id,
            period_end_date=period,
            free_cash_flow=Decimal(
                "150"
            ),
        )
    )
    db_session.commit()

    second = repository.upsert(
        make_cash_flow_data(
            asset_id=asset.id,
            period_end_date=period,
            free_cash_flow=Decimal(
                "225"
            ),
        )
    )
    db_session.commit()

    assert second.id == first.id
    assert (
        second.free_cash_flow
        == Decimal("225")
    )


def test_financial_metrics_repository_get_by_period(
    db_session,
):
    asset = create_asset(db_session)

    period = date(
        2025,
        9,
        30,
    )

    income_repository = (
        IncomeStatementRepository(
            db_session
        )
    )
    balance_repository = (
        BalanceSheetRepository(
            db_session
        )
    )
    cash_repository = (
        CashFlowStatementRepository(
            db_session
        )
    )

    income_repository.create(
        make_income_statement(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    balance_repository.upsert(
        make_balance_sheet_data(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    cash_repository.upsert(
        make_cash_flow_data(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    db_session.commit()

    repository = FinancialMetricsRepository(
        db_session
    )

    result = repository.get_by_period(
        asset_id=asset.id,
        period_end_date=period,
        period_type="annual",
    )

    assert result is not None

    (
        income_statement,
        balance_sheet,
        cash_flow_statement,
    ) = result

    assert income_statement.asset_id == asset.id
    assert balance_sheet.asset_id == asset.id
    assert cash_flow_statement.asset_id == asset.id

    assert (
        income_statement.period_end_date
        == period
    )
    assert (
        balance_sheet.period_end_date
        == period
    )
    assert (
        cash_flow_statement.period_end_date
        == period
    )


def test_financial_metrics_repository_requires_all_three_statements(
    db_session,
):
    asset = create_asset(db_session)

    period = date(
        2025,
        9,
        30,
    )

    IncomeStatementRepository(
        db_session
    ).create(
        make_income_statement(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    BalanceSheetRepository(
        db_session
    ).upsert(
        make_balance_sheet_data(
            asset_id=asset.id,
            period_end_date=period,
        )
    )

    db_session.commit()

    repository = FinancialMetricsRepository(
        db_session
    )

    result = repository.get_by_period(
        asset_id=asset.id,
        period_end_date=period,
        period_type="annual",
    )

    assert result is None


def test_financial_metrics_repository_lists_matched_periods_newest_first(
    db_session,
):
    asset = create_asset(db_session)

    income_repository = (
        IncomeStatementRepository(
            db_session
        )
    )
    balance_repository = (
        BalanceSheetRepository(
            db_session
        )
    )
    cash_repository = (
        CashFlowStatementRepository(
            db_session
        )
    )

    periods = [
        date(2024, 9, 30),
        date(2025, 9, 30),
    ]

    for period in periods:
        income_repository.create(
            make_income_statement(
                asset_id=asset.id,
                period_end_date=period,
            )
        )

        balance_repository.upsert(
            make_balance_sheet_data(
                asset_id=asset.id,
                period_end_date=period,
            )
        )

        cash_repository.upsert(
            make_cash_flow_data(
                asset_id=asset.id,
                period_end_date=period,
            )
        )

        db_session.commit()

    repository = FinancialMetricsRepository(
        db_session
    )

    result = repository.get_matched_periods(
        asset_id=asset.id,
        period_type="annual",
        limit=10,
    )

    assert len(result) == 2

    assert [
        row[0].period_end_date
        for row in result
    ] == [
        date(2025, 9, 30),
        date(2024, 9, 30),
    ]


def test_financial_metrics_repository_filters_period_type(
    db_session,
):
    asset = create_asset(db_session)

    income_repository = (
        IncomeStatementRepository(
            db_session
        )
    )
    balance_repository = (
        BalanceSheetRepository(
            db_session
        )
    )
    cash_repository = (
        CashFlowStatementRepository(
            db_session
        )
    )

    annual_date = date(
        2025,
        9,
        30,
    )
    quarterly_date = date(
        2025,
        6,
        30,
    )

    for period, period_type in [
        (
            annual_date,
            "annual",
        ),
        (
            quarterly_date,
            "quarterly",
        ),
    ]:
        income_repository.create(
            make_income_statement(
                asset_id=asset.id,
                period_end_date=period,
                period_type=period_type,
            )
        )

        balance_repository.upsert(
            make_balance_sheet_data(
                asset_id=asset.id,
                period_end_date=period,
                period_type=period_type,
            )
        )

        cash_repository.upsert(
            make_cash_flow_data(
                asset_id=asset.id,
                period_end_date=period,
                period_type=period_type,
            )
        )

        db_session.commit()

    repository = FinancialMetricsRepository(
        db_session
    )

    result = repository.get_matched_periods(
        asset_id=asset.id,
        period_type="quarterly",
        limit=10,
    )

    assert len(result) == 1
    assert (
        result[0][0].period_type
        == "quarterly"
    )
    assert (
        result[0][0].period_end_date
        == quarterly_date
    )