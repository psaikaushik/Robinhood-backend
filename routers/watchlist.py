from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.watchlist import WatchlistAdd, WatchlistResponse
from services.market import MarketService
from services.auth import get_current_user
from models.user import User
from models.watchlist import Watchlist

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("", response_model=List[WatchlistResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's watchlist."""
    watchlist_items = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).order_by(Watchlist.added_at.desc()).all()

    result = []
    for item in watchlist_items:
        stock = MarketService.get_stock(db, item.symbol)
        change, change_percent = (0.0, 0.0)
        current_price = None

        if stock:
            current_price = stock.current_price
            change, change_percent = MarketService.calculate_change(stock)

        result.append(WatchlistResponse(
            id=item.id,
            symbol=item.symbol,
            added_at=item.added_at,
            current_price=current_price,
            change=change,
            change_percent=change_percent
        ))

    return result


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    item: WatchlistAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a stock to the watchlist."""
    symbol = item.symbol.upper()

    # Verify stock exists
    stock = MarketService.get_stock(db, symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol} not found"
        )

    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{symbol} is already in your watchlist"
        )

    # Add to watchlist
    watchlist_item = Watchlist(
        user_id=current_user.id,
        symbol=symbol
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    change, change_percent = MarketService.calculate_change(stock)

    return WatchlistResponse(
        id=watchlist_item.id,
        symbol=watchlist_item.symbol,
        added_at=watchlist_item.added_at,
        current_price=stock.current_price,
        change=change,
        change_percent=change_percent
    )


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a stock from the watchlist."""
    symbol = symbol.upper()

    watchlist_item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol
    ).first()

    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{symbol} is not in your watchlist"
        )

    db.delete(watchlist_item)
    db.commit()
    return None
