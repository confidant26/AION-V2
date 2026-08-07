from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis import Redis
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
from app.api.ranking import router as ranking_router
from app.api.ttm_financials import router as ttm_financials_router
from app.api.ttm_valuation_metrics import (
    router as ttm_valuation_metrics_router,
)
from app.api.valuation_metrics import router as valuation_metrics_router
from app.api.valuation_score import router as valuation_score_router
from app.api.watchlist import router as watchlist_router
from app.core.config import settings
from app.db.session import engine
from app.providers.resilience import ProviderError


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
app.include_router(ranking_router)
app.include_router(watchlist_router)


@app.exception_handler(ProviderError)
async def provider_error_handler(
    request,
    exc: ProviderError,
):
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
        },
    )


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
            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }


@app.get("/health/readiness")
def readiness_check():
    database_ok = False
    redis_ok = False

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        database_ok = True

    except SQLAlchemyError:
        database_ok = False

    redis_client = None

    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

        redis_ok = bool(
            redis_client.ping()
        )

    except Exception:
        redis_ok = False

    finally:
        if redis_client is not None:
            redis_client.close()

    healthy = (
        database_ok
        and redis_ok
    )

    return JSONResponse(
        status_code=(
            200
            if healthy
            else 503
        ),
        content={
            "status": (
                "ready"
                if healthy
                else "not_ready"
            ),
            "database": (
                "connected"
                if database_ok
                else "disconnected"
            ),
            "redis": (
                "connected"
                if redis_ok
                else "disconnected"
            ),
        },
    )