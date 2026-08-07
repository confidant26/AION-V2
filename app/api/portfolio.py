from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioDeleteResponse,
    PortfolioDetailResponse,
    PortfolioPositionUpsert,
    PortfolioSummaryResponse,
    PositionDeleteResponse,
)
from app.services.portfolio_service import (
    PortfolioAlreadyExistsError,
    PortfolioAssetNotFoundError,
    PortfolioNotFoundError,
    PortfolioPositionNotFoundError,
    PortfolioService,
)


router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


def _service(db: Session, user: User) -> PortfolioService:
    return PortfolioService(db, user_id=user.id)


@router.post("", response_model=PortfolioSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return _service(db, user).create(data)
    except PortfolioAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[PortfolioSummaryResponse])
def list_portfolios(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _service(db, user).list()


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return _service(db, user).get(portfolio_id)
    except PortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{portfolio_id}/positions/{symbol}", response_model=PortfolioDetailResponse)
def upsert_position(portfolio_id: int, symbol: str, data: PortfolioPositionUpsert, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return _service(db, user).upsert_position(portfolio_id=portfolio_id, symbol=symbol, data=data)
    except (PortfolioNotFoundError, PortfolioAssetNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{portfolio_id}/positions/{symbol}", response_model=PositionDeleteResponse)
def delete_position(portfolio_id: int, symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        clean_symbol = _service(db, user).remove_position(portfolio_id=portfolio_id, symbol=symbol)
        return PositionDeleteResponse(message="Portfolio position removed.", symbol=clean_symbol)
    except (PortfolioNotFoundError, PortfolioPositionNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{portfolio_id}", response_model=PortfolioDeleteResponse)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        _service(db, user).delete(portfolio_id)
        return PortfolioDeleteResponse(message="Portfolio deleted.", portfolio_id=portfolio_id)
    except PortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
