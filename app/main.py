from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
from app.api.health import router as health_router
from app.api.income_statement import (
    router as income_statement_router,
)
from app.api.market import router as market_router
from app.api.quality_score import router as quality_score_router
from app.api.ranking import router as ranking_router
from app.api.system import router as system_router
from app.api.ttm_financials import router as ttm_financials_router
from app.api.ttm_valuation_metrics import (
    router as ttm_valuation_metrics_router,
)
from app.api.valuation_metrics import router as valuation_metrics_router
from app.api.valuation_score import router as valuation_score_router
from app.api.watchlist import router as watchlist_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.redis import close_redis_client
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.providers.resilience import ProviderError


configure_logging()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    yield
    close_redis_client()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        RateLimitMiddleware
    )
    application.add_middleware(
        RequestContextMiddleware
    )

    application.include_router(
        health_router
    )
    application.include_router(
        assets_router
    )
    application.include_router(
        market_router
    )
    application.include_router(
        company_router
    )
    application.include_router(
        income_statement_router
    )
    application.include_router(
        balance_sheet_router
    )
    application.include_router(
        cash_flow_statement_router
    )
    application.include_router(
        financial_collection_router
    )
    application.include_router(
        financial_metrics_router
    )
    application.include_router(
        growth_metrics_router
    )
    application.include_router(
        growth_score_router
    )
    application.include_router(
        quality_score_router
    )
    application.include_router(
        valuation_metrics_router
    )
    application.include_router(
        ttm_financials_router
    )
    application.include_router(
        ttm_valuation_metrics_router
    )
    application.include_router(
        valuation_score_router
    )
    application.include_router(
        composite_score_router
    )
    application.include_router(
        ranking_router
    )
    application.include_router(
        watchlist_router
    )
    application.include_router(
        system_router
    )

    @application.exception_handler(
        ProviderError
    )
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

    @application.get("/")
    def root() -> dict[str, str]:
        return {
            "application": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    return application


app = create_app()
