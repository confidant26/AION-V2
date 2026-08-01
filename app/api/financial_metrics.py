from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.financial_metrics import FinancialMetricsResponse
from app.services.financial_metrics_service import (
    FinancialMetricsService,
)


router = APIRouter(
    prefix="/financial-metrics",
    tags=["Financial Metrics"],
)


@router.get(
    "/{symbol}",
    response_model=list[FinancialMetricsResponse],
)
def get_financial_metrics(
    symbol: str,
    period_type: str | None = Query(
        default=None,
        description=(
            "Optional period filter. "
            "Examples: annual, quarterly."
        ),
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of matched periods to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> list[FinancialMetricsResponse]:
    service = FinancialMetricsService(db=db)

    try:
        return service.get_financial_metrics(
            symbol=symbol,
            period_type=period_type,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc