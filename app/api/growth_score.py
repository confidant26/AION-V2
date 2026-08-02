from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.growth_score import GrowthScoreResponse
from app.services.growth_score_service import (
    GrowthScoreService,
)


router = APIRouter(
    prefix="/growth-score",
    tags=["Growth Score"],
)


@router.get(
    "/{symbol}",
    response_model=list[GrowthScoreResponse],
)
def get_growth_scores(
    symbol: str,
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description=(
            "Maximum number of annual growth score periods to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> list[GrowthScoreResponse]:
    service = GrowthScoreService(db=db)

    try:
        return service.get_growth_scores(
            symbol=symbol,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc