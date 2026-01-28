from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.portfolio import PortfolioResponse, HoldingResponse
from services.market import MarketService
from services.auth import get_current_user
from models.user import User
from models.portfolio import PortfolioHolding

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioResponse)
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's portfolio summary."""
    holdings = db.query(PortfolioHolding).filter(
        PortfolioHolding.user_id == current_user.id
    ).all()

    holdings_list = []
    total_holdings_value = 0.0
    total_cost_basis = 0.0

    for holding in holdings:
        stock = MarketService.get_stock(db, holding.symbol)
        current_price = stock.current_price if stock else holding.average_buy_price
        current_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_buy_price
        gain_loss = current_value - cost_basis
        gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0

        total_holdings_value += current_value
        total_cost_basis += cost_basis

        holdings_list.append(HoldingResponse(
            id=holding.id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            average_buy_price=round(holding.average_buy_price, 2),
            current_price=round(current_price, 2),
            current_value=round(current_value, 2),
            total_gain_loss=round(gain_loss, 2),
            gain_loss_percent=round(gain_loss_percent, 2)
        ))

    total_portfolio_value = current_user.balance + total_holdings_value
    total_gain_loss = total_holdings_value - total_cost_basis

    return PortfolioResponse(
        cash_balance=round(current_user.balance, 2),
        total_holdings_value=round(total_holdings_value, 2),
        total_portfolio_value=round(total_portfolio_value, 2),
        total_gain_loss=round(total_gain_loss, 2),
        holdings=holdings_list
    )


@router.get("/holdings", response_model=List[HoldingResponse])
def get_holdings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all stock holdings for the current user."""
    holdings = db.query(PortfolioHolding).filter(
        PortfolioHolding.user_id == current_user.id
    ).all()

    holdings_list = []
    for holding in holdings:
        stock = MarketService.get_stock(db, holding.symbol)
        current_price = stock.current_price if stock else holding.average_buy_price
        current_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_buy_price
        gain_loss = current_value - cost_basis
        gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0

        holdings_list.append(HoldingResponse(
            id=holding.id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            average_buy_price=round(holding.average_buy_price, 2),
            current_price=round(current_price, 2),
            current_value=round(current_value, 2),
            total_gain_loss=round(gain_loss, 2),
            gain_loss_percent=round(gain_loss_percent, 2)
        ))

    return holdings_list


@router.get("/holdings/{symbol}", response_model=HoldingResponse)
def get_holding(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific stock holding."""
    from fastapi import HTTPException, status

    holding = db.query(PortfolioHolding).filter(
        PortfolioHolding.user_id == current_user.id,
        PortfolioHolding.symbol == symbol.upper()
    ).first()

    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No holding found for {symbol.upper()}"
        )

    stock = MarketService.get_stock(db, holding.symbol)
    current_price = stock.current_price if stock else holding.average_buy_price
    current_value = holding.quantity * current_price
    cost_basis = holding.quantity * holding.average_buy_price
    gain_loss = current_value - cost_basis
    gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0

    return HoldingResponse(
        id=holding.id,
        symbol=holding.symbol,
        quantity=holding.quantity,
        average_buy_price=round(holding.average_buy_price, 2),
        current_price=round(current_price, 2),
        current_value=round(current_value, 2),
        total_gain_loss=round(gain_loss, 2),
        gain_loss_percent=round(gain_loss_percent, 2)
    )


@router.get("/balance")
def get_balance(current_user: User = Depends(get_current_user)):
    """Get the current user's cash balance."""
    return {
        "balance": round(current_user.balance, 2),
        "currency": "USD"
    }
