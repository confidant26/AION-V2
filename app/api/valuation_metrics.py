from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.valuation_metrics import ValuationMetricsResponse
from app.services.valuation_metrics_service import (
    ValuationMetricsService,
)


router = APIRouter(
    prefix="/valuation-metrics",
    tags=["Valuation Metrics"],
)


@router.get(
    "/{symbol}",
    response_model=list[ValuationMetricsResponse],
)
def get_valuation_metrics(
    symbol: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of annual valuation periods to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> list[ValuationMetricsResponse]:
    service = ValuationMetricsService(db=db)

    try:
        return service.get_valuation_metrics(
            symbol=symbol,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc