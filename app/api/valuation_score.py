from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.valuation_score import ValuationScoreResponse
from app.services.valuation_score_service import (
    ValuationScoreService,
)


router = APIRouter(
    prefix="/valuation-score",
    tags=["Valuation Score"],
)


@router.get(
    "/{symbol}",
    response_model=ValuationScoreResponse,
)
def get_valuation_score(
    symbol: str,
    db: Session = Depends(get_db),
) -> ValuationScoreResponse:
    service = ValuationScoreService(db=db)

    try:
        return service.get_valuation_score(
            symbol=symbol,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc