from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.balance_sheet_service import (
    BalanceSheetService,
)
from app.services.cash_flow_statement_service import (
    CashFlowStatementService,
)
from app.services.financial_metrics_service import (
    FinancialMetricsService,
)
from app.services.income_statement_service import (
    IncomeStatementService,
)


class FakeAssetRepository:
    def __init__(
        self,
        asset=None,
    ):
        self.asset = asset
        self.requested_symbols = []

    def get_by_symbol(
        self,
        symbol: str,
    ):
        self.requested_symbols.append(
            symbol
        )

        return self.asset


class FakeIncomeProvider:
    def __init__(
        self,
        statements=None,
    ):
        self.statements = (
            statements
            if statements is not None
            else []
        )
        self.requested_symbols = []

    async def get_income_statements(
        self,
        symbol: str,
    ):
        self.requested_symbols.append(
            symbol
        )

        return self.statements


class FakeIncomeStatementRepository:
    def __init__(
        self,
        *,
        existing=None,
        statements=None,
    ):
        self.existing = existing
        self.statements = (
            statements
            if statements is not None
            else []
        )

        self.period_calls = []
        self.create_calls = []
        self.update_calls = []
        self.get_calls = []

    def get_by_asset_and_period(
        self,
        *,
        asset_id: int,
        period_end_date: date,
        period_type: str,
    ):
        self.period_calls.append(
            {
                "asset_id": asset_id,
                "period_end_date": period_end_date,
                "period_type": period_type,
            }
        )

        return self.existing

    def create(
        self,
        statement,
    ):
        self.create_calls.append(
            statement
        )

        return statement

    def update(
        self,
        statement,
    ):
        self.update_calls.append(
            statement
        )

        return statement

    def get_by_asset_id(
        self,
        *,
        asset_id: int,
        limit: int,
    ):
        self.get_calls.append(
            {
                "asset_id": asset_id,
                "limit": limit,
            }
        )

        return self.statements


class FakeStatementRepository:
    def __init__(
        self,
        *,
        statements=None,
        saved=None,
        raise_on_upsert=False,
    ):
        self.statements = (
            statements
            if statements is not None
            else []
        )
        self.saved = saved
        self.raise_on_upsert = (
            raise_on_upsert
        )

        self.upsert_calls = []
        self.get_calls = []

    def upsert(
        self,
        statement,
    ):
        self.upsert_calls.append(
            statement
        )

        if self.raise_on_upsert:
            raise RuntimeError(
                "database write failed"
            )

        if self.saved is not None:
            return self.saved

        return statement

    def get_by_asset_id(
        self,
        *,
        asset_id: int,
        limit: int,
    ):
        self.get_calls.append(
            {
                "asset_id": asset_id,
                "limit": limit,
            }
        )

        return self.statements


class FakeDB:
    def __init__(self):
        self.commit_count = 0
        self.rollback_count = 0
        self.refreshed = []

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def refresh(
        self,
        value,
    ):
        self.refreshed.append(
            value
        )


class FakeFinancialMetricsRepository:
    def __init__(
        self,
        matched_periods=None,
    ):
        self.matched_periods = (
            matched_periods
            if matched_periods is not None
            else []
        )

        self.calls = []

    def get_matched_periods(
        self,
        *,
        asset_id: int,
        period_type,
        limit: int,
    ):
        self.calls.append(
            {
                "asset_id": asset_id,
                "period_type": period_type,
                "limit": limit,
            }
        )

        return self.matched_periods


def make_asset():
    return SimpleNamespace(
        id=7,
        symbol="AAPL",
        currency="USD",
    )


def make_raw_income_statement():
    return {
        "period_end_date": date(
            2025,
            9,
            30,
        ),
        "period_type": "annual",
        "currency": "USD",
        "total_revenue": "1000.9",
        "cost_of_revenue": "400",
        "gross_profit": "600",
        "operating_expense": "200",
        "operating_income": "400.7",
        "net_non_operating_interest_income_expense": "-10",
        "pretax_income": "390",
        "tax_provision": "90",
        "net_income": "300.8",
        "diluted_average_shares": "100.2",
        "diluted_eps": 3.25,
    }


@pytest.mark.anyio
async def test_income_collection_creates_new_statement(
    monkeypatch,
):
    asset = make_asset()

    provider = FakeIncomeProvider(
        [
            make_raw_income_statement()
        ]
    )

    repository = (
        FakeIncomeStatementRepository(
            existing=None
        )
    )

    mapped_statement = (
        SimpleNamespace(
            id=1,
            asset_id=asset.id,
        )
    )

    service = object.__new__(
        IncomeStatementService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=asset
        )
    )
    service.income_statement_repository = (
        repository
    )
    service.provider = provider

    monkeypatch.setattr(
        "app.services.income_statement_service."
        "map_income_statement_create_to_model",
        lambda *,
        data,
        asset_id: mapped_statement,
    )

    result = (
        await service
        .collect_income_statements(
            "  aapl "
        )
    )

    assert result == [
        mapped_statement
    ]

    assert (
        provider.requested_symbols
        == ["AAPL"]
    )

    assert (
        repository.create_calls
        == [mapped_statement]
    )

    assert repository.update_calls == []

    assert repository.period_calls == [
        {
            "asset_id": 7,
            "period_end_date": date(
                2025,
                9,
                30,
            ),
            "period_type": "annual",
        }
    ]


@pytest.mark.anyio
async def test_income_collection_updates_existing_statement():
    asset = make_asset()

    existing = SimpleNamespace(
        currency=None,
        total_revenue=None,
        cost_of_revenue=None,
        gross_profit=None,
        operating_expense=None,
        operating_income=None,
        net_non_operating_interest_income_expense=None,
        pretax_income=None,
        tax_provision=None,
        net_income=None,
        diluted_average_shares=None,
        diluted_eps=None,
    )

    repository = (
        FakeIncomeStatementRepository(
            existing=existing
        )
    )

    service = object.__new__(
        IncomeStatementService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=asset
        )
    )
    service.income_statement_repository = (
        repository
    )
    service.provider = FakeIncomeProvider(
        [
            make_raw_income_statement()
        ]
    )

    result = (
        await service
        .collect_income_statements(
            "aapl"
        )
    )

    assert result == [existing]

    assert repository.create_calls == []
    assert repository.update_calls == [
        existing
    ]

    assert existing.currency == "USD"
    assert existing.total_revenue == 1000
    assert existing.operating_income == 400
    assert existing.net_income == 300
    assert existing.diluted_average_shares == 100
    assert existing.diluted_eps == "3.25"


@pytest.mark.anyio
async def test_income_collection_fails_when_asset_is_missing():
    service = object.__new__(
        IncomeStatementService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=None
        )
    )
    service.income_statement_repository = (
        FakeIncomeStatementRepository()
    )
    service.provider = (
        FakeIncomeProvider()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Asset not found for symbol: AAPL"
        ),
    ):
        await service.collect_income_statements(
            "aapl"
        )


@pytest.mark.anyio
async def test_income_collection_fails_when_provider_returns_nothing():
    service = object.__new__(
        IncomeStatementService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.income_statement_repository = (
        FakeIncomeStatementRepository()
    )
    service.provider = (
        FakeIncomeProvider(
            statements=[]
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Income statements not found for symbol: AAPL"
        ),
    ):
        await service.collect_income_statements(
            "aapl"
        )


def test_income_query_returns_statements_and_passes_limit():
    statements = [
        SimpleNamespace(
            id=1,
        ),
        SimpleNamespace(
            id=2,
        ),
    ]

    asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )

    repository = (
        FakeIncomeStatementRepository(
            statements=statements
        )
    )

    service = object.__new__(
        IncomeStatementService
    )
    service.asset_repository = (
        asset_repository
    )
    service.income_statement_repository = (
        repository
    )

    result = (
        service.get_income_statements(
            symbol="  aapl ",
            limit=5,
        )
    )

    assert result == statements

    assert (
        asset_repository
        .requested_symbols
        == ["AAPL"]
    )

    assert repository.get_calls == [
        {
            "asset_id": 7,
            "limit": 5,
        }
    ]


def test_income_query_fails_when_no_statements_exist():
    service = object.__new__(
        IncomeStatementService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.income_statement_repository = (
        FakeIncomeStatementRepository(
            statements=[]
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Income statements not found for symbol: AAPL"
        ),
    ):
        service.get_income_statements(
            symbol="AAPL",
            limit=20,
        )


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("100.9", 100),
        (100, 100),
        ("nan", None),
        (float("nan"), None),
        ("invalid", None),
        (object(), None),
    ],
)
def test_income_to_int_or_none(
    value,
    expected,
):
    assert (
        IncomeStatementService
        ._to_int_or_none(
            value
        )
        == expected
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("3.20", "3.20"),
        (3.2, "3.2"),
        ("nan", None),
        ("NaN", None),
    ],
)
def test_income_to_string_or_none(
    value,
    expected,
):
    assert (
        IncomeStatementService
        ._to_string_or_none(
            value
        )
        == expected
    )


@pytest.mark.anyio
async def test_balance_sheet_collection_commits_and_refreshes(
    monkeypatch,
):
    asset = make_asset()

    statement_1 = SimpleNamespace(
        id=1,
    )
    statement_2 = SimpleNamespace(
        id=2,
    )

    saved_1 = SimpleNamespace(
        id=11,
    )
    saved_2 = SimpleNamespace(
        id=12,
    )

    db = FakeDB()

    repository = (
        FakeStatementRepository()
    )

    saved_values = iter(
        [
            saved_1,
            saved_2,
        ]
    )

    def fake_upsert(
        statement,
    ):
        repository.upsert_calls.append(
            statement
        )
        return next(saved_values)

    repository.upsert = fake_upsert

    monkeypatch.setattr(
        "app.services.balance_sheet_service."
        "YahooBalanceSheetProvider.fetch",
        lambda *,
        asset_id,
        symbol,
        currency: [
            statement_1,
            statement_2,
        ],
    )

    service = object.__new__(
        BalanceSheetService
    )
    service.db = db
    service.asset_repository = (
        FakeAssetRepository(
            asset=asset
        )
    )
    service.balance_sheet_repository = (
        repository
    )

    result = (
        await service
        .collect_balance_sheets(
            " aapl "
        )
    )

    assert result == [
        saved_1,
        saved_2,
    ]

    assert repository.upsert_calls == [
        statement_1,
        statement_2,
    ]

    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert db.refreshed == [
        saved_1,
        saved_2,
    ]


@pytest.mark.anyio
async def test_balance_sheet_collection_rolls_back_on_failure(
    monkeypatch,
):
    db = FakeDB()

    monkeypatch.setattr(
        "app.services.balance_sheet_service."
        "YahooBalanceSheetProvider.fetch",
        lambda **kwargs: [
            SimpleNamespace(
                id=1,
            )
        ],
    )

    service = object.__new__(
        BalanceSheetService
    )
    service.db = db
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.balance_sheet_repository = (
        FakeStatementRepository(
            raise_on_upsert=True
        )
    )

    with pytest.raises(
        RuntimeError,
        match="database write failed",
    ):
        await service.collect_balance_sheets(
            "AAPL"
        )

    assert db.commit_count == 0
    assert db.rollback_count == 1


@pytest.mark.anyio
async def test_balance_sheet_collection_fails_when_provider_is_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.balance_sheet_service."
        "YahooBalanceSheetProvider.fetch",
        lambda **kwargs: [],
    )

    service = object.__new__(
        BalanceSheetService
    )
    service.db = FakeDB()
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.balance_sheet_repository = (
        FakeStatementRepository()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Balance sheets not found for symbol: AAPL"
        ),
    ):
        await service.collect_balance_sheets(
            "aapl"
        )


def test_balance_sheet_query_returns_statements():
    statements = [
        SimpleNamespace(
            id=1,
        )
    ]

    repository = (
        FakeStatementRepository(
            statements=statements
        )
    )

    service = object.__new__(
        BalanceSheetService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.balance_sheet_repository = (
        repository
    )

    result = (
        service.get_balance_sheets(
            symbol=" aapl ",
            limit=8,
        )
    )

    assert result == statements

    assert repository.get_calls == [
        {
            "asset_id": 7,
            "limit": 8,
        }
    ]


@pytest.mark.anyio
async def test_cash_flow_collection_commits_and_refreshes(
    monkeypatch,
):
    statement_1 = SimpleNamespace(
        id=1,
    )
    statement_2 = SimpleNamespace(
        id=2,
    )

    saved_1 = SimpleNamespace(
        id=21,
    )
    saved_2 = SimpleNamespace(
        id=22,
    )

    db = FakeDB()

    repository = (
        FakeStatementRepository()
    )

    saved_values = iter(
        [
            saved_1,
            saved_2,
        ]
    )

    def fake_upsert(
        statement,
    ):
        repository.upsert_calls.append(
            statement
        )
        return next(saved_values)

    repository.upsert = fake_upsert

    monkeypatch.setattr(
        "app.services.cash_flow_statement_service."
        "YahooCashFlowProvider.fetch",
        lambda *,
        asset_id,
        symbol,
        currency: [
            statement_1,
            statement_2,
        ],
    )

    service = object.__new__(
        CashFlowStatementService
    )
    service.db = db
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.cash_flow_statement_repository = (
        repository
    )

    result = (
        await service
        .collect_cash_flow_statements(
            " aapl "
        )
    )

    assert result == [
        saved_1,
        saved_2,
    ]

    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert db.refreshed == [
        saved_1,
        saved_2,
    ]


@pytest.mark.anyio
async def test_cash_flow_collection_rolls_back_on_failure(
    monkeypatch,
):
    db = FakeDB()

    monkeypatch.setattr(
        "app.services.cash_flow_statement_service."
        "YahooCashFlowProvider.fetch",
        lambda **kwargs: [
            SimpleNamespace(
                id=1,
            )
        ],
    )

    service = object.__new__(
        CashFlowStatementService
    )
    service.db = db
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.cash_flow_statement_repository = (
        FakeStatementRepository(
            raise_on_upsert=True
        )
    )

    with pytest.raises(
        RuntimeError,
        match="database write failed",
    ):
        await service.collect_cash_flow_statements(
            "AAPL"
        )

    assert db.commit_count == 0
    assert db.rollback_count == 1


@pytest.mark.anyio
async def test_cash_flow_collection_fails_when_provider_is_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.cash_flow_statement_service."
        "YahooCashFlowProvider.fetch",
        lambda **kwargs: [],
    )

    service = object.__new__(
        CashFlowStatementService
    )
    service.db = FakeDB()
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.cash_flow_statement_repository = (
        FakeStatementRepository()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Cash flow statements not found for symbol: AAPL"
        ),
    ):
        await service.collect_cash_flow_statements(
            "aapl"
        )


def test_cash_flow_query_returns_statements():
    statements = [
        SimpleNamespace(
            id=1,
        )
    ]

    repository = (
        FakeStatementRepository(
            statements=statements
        )
    )

    service = object.__new__(
        CashFlowStatementService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.cash_flow_statement_repository = (
        repository
    )

    result = (
        service.get_cash_flow_statements(
            symbol=" aapl ",
            limit=9,
        )
    )

    assert result == statements

    assert repository.get_calls == [
        {
            "asset_id": 7,
            "limit": 9,
        }
    ]


def make_matched_financial_period(
    *,
    total_revenue=1000,
    operating_income=250,
    net_income=200,
    current_assets=600,
    current_liabilities=300,
    total_debt=400,
    stockholders_equity=800,
    total_assets=2000,
    free_cash_flow=150,
):
    income_statement = (
        SimpleNamespace(
            id=1,
            period_end_date=date(
                2025,
                9,
                30,
            ),
            period_type="annual",
            currency="USD",
            total_revenue=total_revenue,
            operating_income=operating_income,
            net_income=net_income,
        )
    )

    balance_sheet = (
        SimpleNamespace(
            id=2,
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            total_debt=total_debt,
            stockholders_equity=stockholders_equity,
            total_assets=total_assets,
        )
    )

    cash_flow_statement = (
        SimpleNamespace(
            id=3,
            free_cash_flow=free_cash_flow,
        )
    )

    return (
        income_statement,
        balance_sheet,
        cash_flow_statement,
    )


def test_financial_metrics_calculates_expected_values():
    repository = (
        FakeFinancialMetricsRepository(
            matched_periods=[
                make_matched_financial_period()
            ]
        )
    )

    service = object.__new__(
        FinancialMetricsService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.financial_metrics_repository = (
        repository
    )

    result = (
        service.get_financial_metrics(
            symbol=" aapl ",
            period_type="annual",
            limit=5,
        )
    )

    assert len(result) == 1

    metrics = result[0]

    assert metrics.symbol == "AAPL"

    assert (
        metrics.operating_margin
        == Decimal("0.25")
    )

    assert (
        metrics.net_margin
        == Decimal("0.2")
    )

    assert (
        metrics.current_ratio
        == Decimal("2")
    )

    assert (
        metrics.debt_to_equity
        == Decimal("0.5")
    )

    assert (
        metrics.return_on_assets
        == Decimal("0.1")
    )

    assert (
        metrics.return_on_equity
        == Decimal("0.25")
    )

    assert (
        metrics.free_cash_flow_margin
        == Decimal("0.15")
    )

    assert metrics.missing_fields == []
    assert metrics.confidence == Decimal("1")

    assert repository.calls == [
        {
            "asset_id": 7,
            "period_type": "annual",
            "limit": 5,
        }
    ]


def test_financial_metrics_tracks_missing_fields_and_confidence():
    repository = (
        FakeFinancialMetricsRepository(
            matched_periods=[
                make_matched_financial_period(
                    total_revenue=None,
                    net_income=None,
                    current_assets=None,
                )
            ]
        )
    )

    service = object.__new__(
        FinancialMetricsService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.financial_metrics_repository = (
        repository
    )

    result = (
        service.get_financial_metrics(
            symbol="AAPL"
        )
    )

    metrics = result[0]

    assert set(
        metrics.missing_fields
    ) == {
        "total_revenue",
        "net_income",
        "current_assets",
    }

    assert (
        metrics.confidence
        == Decimal("6")
        / Decimal("9")
    )

    assert metrics.operating_margin is None
    assert metrics.net_margin is None
    assert metrics.current_ratio is None
    assert metrics.return_on_assets is None
    assert metrics.return_on_equity is None
    assert metrics.free_cash_flow_margin is None


def test_financial_metrics_fails_when_asset_is_missing():
    service = object.__new__(
        FinancialMetricsService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=None
        )
    )
    service.financial_metrics_repository = (
        FakeFinancialMetricsRepository()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Asset not found for symbol: AAPL"
        ),
    ):
        service.get_financial_metrics(
            "aapl"
        )


def test_financial_metrics_fails_when_periods_are_missing():
    service = object.__new__(
        FinancialMetricsService
    )
    service.asset_repository = (
        FakeAssetRepository(
            asset=make_asset()
        )
    )
    service.financial_metrics_repository = (
        FakeFinancialMetricsRepository(
            matched_periods=[]
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Matched financial statements not found for symbol: AAPL"
        ),
    ):
        service.get_financial_metrics(
            "AAPL"
        )


@pytest.mark.parametrize(
    "numerator, denominator, expected",
    [
        (
            Decimal("10"),
            Decimal("2"),
            Decimal("5"),
        ),
        (
            None,
            Decimal("2"),
            None,
        ),
        (
            Decimal("10"),
            None,
            None,
        ),
        (
            Decimal("10"),
            Decimal("0"),
            None,
        ),
    ],
)
def test_financial_metrics_safe_divide(
    numerator,
    denominator,
    expected,
):
    assert (
        FinancialMetricsService
        ._safe_divide(
            numerator,
            denominator,
        )
        == expected
    )


@pytest.mark.parametrize(
    "value, expected, missing",
    [
        (
            "12.5",
            Decimal("12.5"),
            [],
        ),
        (
            None,
            None,
            ["field"],
        ),
        (
            "invalid",
            None,
            ["field"],
        ),
    ],
)
def test_financial_metrics_decimal_or_none(
    value,
    expected,
    missing,
):
    missing_fields = []

    result = (
        FinancialMetricsService
        ._decimal_or_none(
            value,
            "field",
            missing_fields,
        )
    )

    assert result == expected
    assert missing_fields == missing


@pytest.mark.parametrize(
    "missing_fields, total_fields, expected",
    [
        (
            [],
            9,
            Decimal("1"),
        ),
        (
            ["a"],
            9,
            Decimal("8")
            / Decimal("9"),
        ),
        (
            ["a", "a"],
            9,
            Decimal("8")
            / Decimal("9"),
        ),
        (
            [
                "a",
                "b",
                "c",
            ],
            3,
            Decimal("0"),
        ),
    ],
)
def test_financial_metrics_confidence(
    missing_fields,
    total_fields,
    expected,
):
    assert (
        FinancialMetricsService
        ._calculate_confidence(
            missing_fields=missing_fields,
            total_fields=total_fields,
        )
        == expected
    )