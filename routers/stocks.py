from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.stock import StockResponse
from services.market import MarketService
from services.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("", response_model=List[StockResponse])
def get_all_stocks(db: Session = Depends(get_db)):
    """Get all available stocks."""
    stocks = MarketService.get_all_stocks(db)
    result = []
    for stock in stocks:
        change, change_percent = MarketService.calculate_change(stock)
        stock_dict = {
            "id": stock.id,
            "symbol": stock.symbol,
            "name": stock.name,
            "current_price": stock.current_price,
            "previous_close": stock.previous_close,
            "day_high": stock.day_high,
            "day_low": stock.day_low,
            "volume": stock.volume,
            "market_cap": stock.market_cap,
            "sector": stock.sector,
            "change": change,
            "change_percent": change_percent,
            "updated_at": stock.updated_at
        }
        result.append(StockResponse(**stock_dict))
    return result


@router.get("/search")
def search_stocks(q: str, db: Session = Depends(get_db)):
    """Search stocks by symbol or name."""
    if len(q) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 1 character"
        )

    stocks = MarketService.search_stocks(db, q)
    result = []
    for stock in stocks:
        change, change_percent = MarketService.calculate_change(stock)
        result.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "current_price": stock.current_price,
            "change": change,
            "change_percent": change_percent
        })
    return result


@router.get("/{symbol}", response_model=StockResponse)
def get_stock(symbol: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific stock."""
    stock = MarketService.get_stock(db, symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol.upper()} not found"
        )

    change, change_percent = MarketService.calculate_change(stock)
    return StockResponse(
        id=stock.id,
        symbol=stock.symbol,
        name=stock.name,
        current_price=stock.current_price,
        previous_close=stock.previous_close,
        day_high=stock.day_high,
        day_low=stock.day_low,
        volume=stock.volume,
        market_cap=stock.market_cap,
        sector=stock.sector,
        change=change,
        change_percent=change_percent,
        updated_at=stock.updated_at
    )


@router.get("/{symbol}/quote")
def get_stock_quote(symbol: str, db: Session = Depends(get_db)):
    """Get a quick quote for a stock."""
    stock = MarketService.get_stock(db, symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol.upper()} not found"
        )

    change, change_percent = MarketService.calculate_change(stock)
    return {
        "symbol": stock.symbol,
        "price": stock.current_price,
        "change": change,
        "change_percent": change_percent
    }


@router.post("/{symbol}/simulate")
def simulate_price_change(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulate a price change for a stock (for testing purposes)."""
    stock = MarketService.simulate_price_change(db, symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol.upper()} not found"
        )

    change, change_percent = MarketService.calculate_change(stock)
    return {
        "symbol": stock.symbol,
        "new_price": stock.current_price,
        "change": change,
        "change_percent": change_percent
    }


@router.post("/simulate-all")
def simulate_all_prices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulate price changes for all stocks (for testing purposes)."""
    stocks = MarketService.simulate_all_prices(db)
    return {"message": f"Simulated price changes for {len(stocks)} stocks"}
