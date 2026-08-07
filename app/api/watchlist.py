from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.watchlist import WatchlistDeleteResponse, WatchlistItemResponse, WatchlistResponse
from app.services.watchlist_service import (
    WatchlistAlreadyExistsError,
    WatchlistAssetNotFoundError,
    WatchlistItemNotFoundError,
    WatchlistService,
)


router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


def _service(db: Session, user: User) -> WatchlistService:
    return WatchlistService(db=db, user_id=user.id)


@router.post("/{symbol}", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> WatchlistItemResponse:
    try:
        return _service(db, user).add(symbol)
    except WatchlistAssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WatchlistAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=WatchlistResponse)
def list_watchlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> WatchlistResponse:
    items = _service(db, user).list_items()
    return WatchlistResponse(count=len(items), results=items)


@router.get("/{symbol}", response_model=WatchlistItemResponse)
def get_watchlist_item(symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> WatchlistItemResponse:
    try:
        return _service(db, user).get(symbol)
    except WatchlistItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{symbol}", response_model=WatchlistDeleteResponse)
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> WatchlistDeleteResponse:
    try:
        clean_symbol = _service(db, user).remove(symbol)
        return WatchlistDeleteResponse(message="Asset removed from watchlist.", symbol=clean_symbol)
    except WatchlistItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
