from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.assets import router as assets_router
from app.api.balance_sheet import router as balance_sheet_router
from app.api.cash_flow_statement import (
    router as cash_flow_statement_router,
)
from app.api.company import router as company_router
from app.api.composite_score import router as composite_score_router
from app.api.financial_collection import (
    router as financial_collection_router,
)
from app.api.financial_metrics import router as financial_metrics_router
from app.api.growth_metrics import router as growth_metrics_router
from app.api.growth_score import router as growth_score_router
from app.api.income_statement import (
    router as income_statement_router,
)
from app.api.market import router as market_router
from app.api.quality_score import router as quality_score_router
from app.api.ttm_financials import router as ttm_financials_router
from app.api.ttm_valuation_metrics import (
    router as ttm_valuation_metrics_router,
)
from app.api.valuation_metrics import router as valuation_metrics_router
from app.api.valuation_score import router as valuation_score_router
from app.core.config import settings
from app.db.session import engine


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


app.include_router(assets_router)
app.include_router(market_router)
app.include_router(company_router)
app.include_router(income_statement_router)
app.include_router(balance_sheet_router)
app.include_router(cash_flow_statement_router)
app.include_router(financial_collection_router)
app.include_router(financial_metrics_router)
app.include_router(growth_metrics_router)
app.include_router(growth_score_router)
app.include_router(quality_score_router)
app.include_router(valuation_metrics_router)
app.include_router(ttm_financials_router)
app.include_router(ttm_valuation_metrics_router)
app.include_router(valuation_score_router)
app.include_router(composite_score_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@app.get("/health/database")
def database_health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }
