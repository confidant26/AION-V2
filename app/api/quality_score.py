from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.quality_score import QualityScoreResponse
from app.services.quality_score_service import (
    QualityScoreService,
)


router = APIRouter(
    prefix="/quality-score",
    tags=["Quality Score"],
)


@router.get(
    "/{symbol}",
    response_model=list[QualityScoreResponse],
)
def get_quality_scores(
    symbol: str,
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description=(
            "Maximum number of annual quality score periods to return."
        ),
    ),
    db: Session = Depends(get_db),
) -> list[QualityScoreResponse]:
    service = QualityScoreService(db=db)

    try:
        return service.get_quality_scores(
            symbol=symbol,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc