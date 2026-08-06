from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class FakeIncomeStatementService:
    def __init__(
        self,
        db,
        provider,
    ):
        pass

    async def collect_income_statements(
        self,
        symbol,
    ):
        return [
            object(),
            object(),
        ]


class FakeBalanceSheetService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_balance_sheets(
        self,
        symbol,
    ):
        return [
            object(),
            object(),
            object(),
        ]


class FakeCashFlowStatementService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_cash_flow_statements(
        self,
        symbol,
    ):
        return [
            object(),
            object(),
            object(),
            object(),
        ]


def test_financial_collection_endpoint_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.BalanceSheetService",
        FakeBalanceSheetService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"

    assert body["counts"] == {
        "income_statements": 2,
        "balance_sheets": 3,
        "cash_flow_statements": 4,
    }

    assert body["total_count"] == 9


class FakeIncomeStatementNotFoundService:
    def __init__(
        self,
        db,
        provider,
    ):
        pass

    async def collect_income_statements(
        self,
        symbol,
    ):
        raise ValueError(
            "Asset not found for symbol: INVALID"
        )


def test_financial_collection_endpoint_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementNotFoundService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/INVALID"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Asset not found for symbol: INVALID"
    )