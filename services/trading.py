from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user import User
from models.order import Order
from models.portfolio import PortfolioHolding
from models.stock import Stock
from schemas.order import OrderCreate
from services.market import MarketService


class TradingService:
    @staticmethod
    def place_order(db: Session, user: User, order_data: OrderCreate) -> Order:
        """Place a buy or sell order."""
        symbol = order_data.symbol.upper()

        # Verify stock exists
        stock = MarketService.get_stock(db, symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {symbol} not found"
            )

        # Get current price
        current_price = stock.current_price

        # For limit orders, validate limit price
        if order_data.order_type == "limit":
            if not order_data.limit_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Limit price is required for limit orders"
                )
            execution_price = order_data.limit_price
        else:
            execution_price = current_price

        # Create the order
        order = Order(
            user_id=user.id,
            symbol=symbol,
            order_type=order_data.order_type,
            side=order_data.side,
            quantity=order_data.quantity,
            limit_price=order_data.limit_price,
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # For market orders, execute immediately
        if order_data.order_type == "market":
            order = TradingService._execute_order(db, order, user, execution_price)

        # For limit orders, check if it can be filled immediately
        elif order_data.order_type == "limit":
            can_execute = False
            if order_data.side == "buy" and order_data.limit_price >= current_price:
                can_execute = True
                execution_price = current_price  # Execute at better price
            elif order_data.side == "sell" and order_data.limit_price <= current_price:
                can_execute = True
                execution_price = current_price  # Execute at better price

            if can_execute:
                order = TradingService._execute_order(db, order, user, execution_price)

        return order

    @staticmethod
    def _execute_order(db: Session, order: Order, user: User, price: float) -> Order:
        """Execute an order at the given price."""
        total_cost = price * order.quantity

        if order.side == "buy":
            # Check if user has enough balance
            if user.balance < total_cost:
                order.status = "rejected"
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient funds. Required: ${total_cost:.2f}, Available: ${user.balance:.2f}"
                )

            # Deduct from balance
            user.balance -= total_cost

            # Update or create portfolio holding
            holding = db.query(PortfolioHolding).filter(
                PortfolioHolding.user_id == user.id,
                PortfolioHolding.symbol == order.symbol
            ).first()

            if holding:
                # Calculate new average price
                total_shares = holding.quantity + order.quantity
                total_value = (holding.quantity * holding.average_buy_price) + (order.quantity * price)
                holding.average_buy_price = total_value / total_shares
                holding.quantity = total_shares
            else:
                holding = PortfolioHolding(
                    user_id=user.id,
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_buy_price=price
                )
                db.add(holding)

        elif order.side == "sell":
            # Check if user has enough shares
            holding = db.query(PortfolioHolding).filter(
                PortfolioHolding.user_id == user.id,
                PortfolioHolding.symbol == order.symbol
            ).first()

            if not holding or holding.quantity < order.quantity:
                order.status = "rejected"
                db.commit()
                available = holding.quantity if holding else 0
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient shares. Required: {order.quantity}, Available: {available}"
                )

            # Add to balance
            user.balance += total_cost

            # Update holding
            holding.quantity -= order.quantity
            if holding.quantity == 0:
                db.delete(holding)

        # Update order status
        order.filled_quantity = order.quantity
        order.filled_price = price
        order.status = "filled"
        order.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def cancel_order(db: Session, user: User, order_id: int) -> Order:
        """Cancel a pending order."""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user.id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status: {order.status}"
            )

        order.status = "cancelled"
        order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_orders(db: Session, user: User, status_filter: Optional[str] = None) -> List[Order]:
        """Get all orders for a user, optionally filtered by status."""
        query = db.query(Order).filter(Order.user_id == user.id)
        if status_filter:
            query = query.filter(Order.status == status_filter)
        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order(db: Session, user: User, order_id: int) -> Order:
        """Get a specific order."""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user.id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order
