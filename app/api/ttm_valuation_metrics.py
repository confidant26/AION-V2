from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.ttm_valuation_metrics import (
    TTMValuationMetricsResponse,
)
from app.services.ttm_valuation_metrics_service import (
    TTMValuationMetricsService,
)


router = APIRouter(
    prefix="/ttm-valuation-metrics",
    tags=["TTM Valuation Metrics"],
)


@router.get(
    "/{symbol}",
    response_model=TTMValuationMetricsResponse,
)
def get_ttm_valuation_metrics(
    symbol: str,
    db: Session = Depends(get_db),
) -> TTMValuationMetricsResponse:
    service = TTMValuationMetricsService(db=db)

    try:
        return service.get_ttm_valuation_metrics(
            symbol=symbol,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc