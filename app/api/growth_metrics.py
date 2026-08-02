from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.growth_metrics import GrowthMetricsResponse
from app.services.growth_metrics_service import (
    GrowthMetricsService,
)


router = APIRouter(
    prefix="/growth-metrics",
    tags=["Growth Metrics"],
)


@router.get(
    "/{symbol}",
    response_model=list[GrowthMetricsResponse],
)
def get_growth_metrics(
    symbol: str,
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description=(
            "Maximum number of annual growth comparisons to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> list[GrowthMetricsResponse]:
    service = GrowthMetricsService(db=db)

    try:
        return service.get_growth_metrics(
            symbol=symbol,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc