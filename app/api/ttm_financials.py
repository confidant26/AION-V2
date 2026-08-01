from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.ttm_financials import TTMFinancialsResponse
from app.services.ttm_financials_service import (
    TTMFinancialsService,
)


router = APIRouter(
    prefix="/ttm-financials",
    tags=["TTM Financials"],
)


@router.get(
    "/{symbol}",
    response_model=TTMFinancialsResponse,
)
def get_ttm_financials(
    symbol: str,
    db: Session = Depends(get_db),
) -> TTMFinancialsResponse:
    service = TTMFinancialsService(db=db)

    try:
        return service.get_ttm_financials(
            symbol=symbol,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc