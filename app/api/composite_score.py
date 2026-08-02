from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.composite_score import CompositeScoreResponse
from app.services.composite_score_service import (
    CompositeScoreService,
)


router = APIRouter(
    prefix="/composite-score",
    tags=["Composite Score"],
)


@router.get(
    "/{symbol}",
    response_model=CompositeScoreResponse,
)
def get_composite_score(
    symbol: str,
    db: Session = Depends(get_db),
) -> CompositeScoreResponse:
    service = CompositeScoreService(db=db)

    try:
        return service.get_composite_score(
            symbol=symbol,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc