from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.db.dependencies import get_db
from app.main import app


class FakeDB:
    pass


def override_get_db():
    yield FakeDB()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def make_income_statement():
    return SimpleNamespace(
        id=1,
        asset_id=1,
        period_end_date=date(2025, 9, 30),
        period_type="annual",
        currency="USD",
        total_revenue=1000,
        cost_of_revenue=400,
        gross_profit=600,
        operating_expense=200,
        operating_income=400,
        net_non_operating_interest_income_expense=-10,
        pretax_income=390,
        tax_provision=90,
        net_income=300,
        diluted_average_shares=100,
        diluted_eps="3.00",
    )


def make_balance_sheet():
    return SimpleNamespace(
        id=1,
        asset_id=1,
        period_end_date=date(2025, 9, 30),
        period_type="annual",
        currency="USD",
        total_assets=Decimal("5000"),
        current_assets=Decimal("1800"),
        cash_and_cash_equivalents=Decimal("500"),
        inventory=Decimal("300"),
        total_liabilities=Decimal("3000"),
        current_liabilities=Decimal("1200"),
        long_term_debt=Decimal("800"),
        stockholders_equity=Decimal("2000"),
    )


def make_cash_flow_statement():
    return SimpleNamespace(
        id=1,
        asset_id=1,
        period_end_date=date(2025, 9, 30),
        period_type="annual",
        currency="USD",
        operating_cash_flow=Decimal("500"),
        investing_cash_flow=Decimal("-200"),
        financing_cash_flow=Decimal("-100"),
        capital_expenditure=Decimal("-150"),
        free_cash_flow=Decimal("350"),
        depreciation_and_amortization=Decimal("80"),
        stock_based_compensation=Decimal("30"),
        change_in_working_capital=Decimal("-20"),
        dividends_paid=Decimal("-50"),
        share_repurchases=Decimal("-70"),
        debt_issuance=Decimal("100"),
        debt_repayment=Decimal("-60"),
        net_change_in_cash=Decimal("200"),
    )


class FakeIncomeStatementService:
    def __init__(
        self,
        db,
        provider,
    ):
        self.db = db
        self.provider = provider

    def get_income_statements(
        self,
        symbol: str,
        limit: int = 20,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            make_income_statement()
        ][:limit]

    async def collect_income_statements(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            make_income_statement()
        ]


class FakeBalanceSheetService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def get_balance_sheets(
        self,
        symbol: str,
        limit: int = 20,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            make_balance_sheet()
        ][:limit]

    async def collect_balance_sheets(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            make_balance_sheet()
        ]


class FakeCashFlowStatementService:
    def __init__(
        self,
        db,
    ):
        self.db = db

    def get_cash_flow_statements(
        self,
        symbol: str,
        limit: int = 20,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            make_cash_flow_statement()
        ][:limit]

    async def collect_cash_flow_statements(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        if clean_symbol == "INVALID":
            raise ValueError(
                "Asset not found for symbol: INVALID"
            )

        return [
            make_cash_flow_statement()
        ]


def patch_income_dependencies(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.income_statement.IncomeStatementService",
        FakeIncomeStatementService,
    )

    monkeypatch.setattr(
        "app.api.income_statement.get_financial_data_provider",
        lambda: object(),
    )


def test_income_statements_get_success(
    monkeypatch,
):
    patch_income_dependencies(
        monkeypatch
    )

    response = client.get(
        "/income-statements/aapl?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["count"] == 1
    assert body["limit"] == 5

    statement = body["statements"][0]

    assert statement["id"] == 1
    assert statement["asset_id"] == 1
    assert statement["period_type"] == "annual"
    assert statement["currency"] == "USD"
    assert statement["total_revenue"] == 1000
    assert statement["operating_income"] == 400
    assert statement["net_income"] == 300
    assert statement["diluted_eps"] == "3.00"


def test_income_statements_get_returns_404(
    monkeypatch,
):
    patch_income_dependencies(
        monkeypatch
    )

    response = client.get(
        "/income-statements/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_income_statements_reject_invalid_limit():
    assert client.get(
        "/income-statements/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/income-statements/AAPL?limit=101"
    ).status_code == 422


def test_income_statements_collect_success(
    monkeypatch,
):
    patch_income_dependencies(
        monkeypatch
    )

    response = client.post(
        "/income-statements/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == (
        "Income statements collected successfully."
    )
    assert body["symbol"] == "AAPL"
    assert body["count"] == 1
    assert body["statements"][0]["net_income"] == 300


def test_income_statements_collect_returns_404(
    monkeypatch,
):
    patch_income_dependencies(
        monkeypatch
    )

    response = client.post(
        "/income-statements/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_balance_sheets_get_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.balance_sheet.BalanceSheetService",
        FakeBalanceSheetService,
    )

    response = client.get(
        "/balance-sheets/aapl?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["count"] == 1
    assert body["limit"] == 5

    statement = body["statements"][0]

    assert statement["id"] == 1
    assert statement["asset_id"] == 1
    assert statement["period_type"] == "annual"
    assert statement["currency"] == "USD"
    assert statement["total_assets"] == "5000"
    assert statement["current_assets"] == "1800"
    assert statement["long_term_debt"] == "800"
    assert statement["stockholders_equity"] == "2000"


def test_balance_sheets_get_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.balance_sheet.BalanceSheetService",
        FakeBalanceSheetService,
    )

    response = client.get(
        "/balance-sheets/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_balance_sheets_reject_invalid_limit():
    assert client.get(
        "/balance-sheets/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/balance-sheets/AAPL?limit=101"
    ).status_code == 422


def test_balance_sheets_collect_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.balance_sheet.BalanceSheetService",
        FakeBalanceSheetService,
    )

    response = client.post(
        "/balance-sheets/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == (
        "Balance sheets collected successfully."
    )
    assert body["symbol"] == "AAPL"
    assert body["count"] == 1
    assert body["statements"][0]["total_assets"] == "5000"


def test_balance_sheets_collect_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.balance_sheet.BalanceSheetService",
        FakeBalanceSheetService,
    )

    response = client.post(
        "/balance-sheets/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_cash_flow_statements_get_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.cash_flow_statement.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    response = client.get(
        "/cash-flow-statements/aapl?limit=5"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"
    assert body["count"] == 1
    assert body["limit"] == 5

    statement = body["statements"][0]

    assert statement["id"] == 1
    assert statement["asset_id"] == 1
    assert statement["period_type"] == "annual"
    assert statement["currency"] == "USD"
    assert statement["operating_cash_flow"] == "500"
    assert statement["capital_expenditure"] == "-150"
    assert statement["free_cash_flow"] == "350"
    assert statement["net_change_in_cash"] == "200"


def test_cash_flow_statements_get_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.cash_flow_statement.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    response = client.get(
        "/cash-flow-statements/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }


def test_cash_flow_statements_reject_invalid_limit():
    assert client.get(
        "/cash-flow-statements/AAPL?limit=0"
    ).status_code == 422

    assert client.get(
        "/cash-flow-statements/AAPL?limit=101"
    ).status_code == 422


def test_cash_flow_statements_collect_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.cash_flow_statement.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    response = client.post(
        "/cash-flow-statements/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == (
        "Cash flow statements collected successfully."
    )
    assert body["symbol"] == "AAPL"
    assert body["count"] == 1
    assert body["statements"][0]["free_cash_flow"] == "350"


def test_cash_flow_statements_collect_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.cash_flow_statement.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    response = client.post(
        "/cash-flow-statements/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Asset not found for symbol: INVALID"
        )
    }