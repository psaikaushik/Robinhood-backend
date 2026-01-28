import random
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from models.stock import Stock
from services.data_loader import get_data_loader


class MarketService:
    @staticmethod
    def initialize_stocks(db: Session) -> None:
        """Initialize the database with stock data from JSON file."""
        loader = get_data_loader()
        stocks_data = loader.get_stocks()

        for stock_data in stocks_data:
            existing = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()
            if not existing:
                stock = Stock(
                    symbol=stock_data["symbol"],
                    name=stock_data["name"],
                    current_price=stock_data["current_price"],
                    previous_close=stock_data.get("previous_close", stock_data["current_price"]),
                    day_high=stock_data.get("day_high", stock_data["current_price"]),
                    day_low=stock_data.get("day_low", stock_data["current_price"]),
                    volume=stock_data.get("volume", random.randint(1000000, 50000000)),
                    market_cap=stock_data.get("market_cap"),
                    sector=stock_data.get("sector")
                )
                db.add(stock)
        db.commit()

    @staticmethod
    def get_stock(db: Session, symbol: str) -> Optional[Stock]:
        """Get a stock by symbol."""
        return db.query(Stock).filter(Stock.symbol == symbol.upper()).first()

    @staticmethod
    def get_all_stocks(db: Session) -> List[Stock]:
        """Get all available stocks."""
        return db.query(Stock).all()

    @staticmethod
    def search_stocks(db: Session, query: str) -> List[Stock]:
        """Search stocks by symbol or name."""
        query = query.upper()
        return db.query(Stock).filter(
            (Stock.symbol.contains(query)) | (Stock.name.ilike(f"%{query}%"))
        ).all()

    @staticmethod
    def simulate_price_change(db: Session, symbol: str) -> Optional[Stock]:
        """Simulate a small price change for a stock (for demo purposes)."""
        stock = MarketService.get_stock(db, symbol)
        if stock:
            # Random price change between -2% and +2%
            change_percent = random.uniform(-0.02, 0.02)
            new_price = round(stock.current_price * (1 + change_percent), 2)

            stock.current_price = new_price
            stock.day_high = max(stock.day_high or new_price, new_price)
            stock.day_low = min(stock.day_low or new_price, new_price)
            stock.volume += random.randint(1000, 100000)
            stock.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(stock)
        return stock

    @staticmethod
    def simulate_all_prices(db: Session) -> List[Stock]:
        """Simulate price changes for all stocks."""
        stocks = MarketService.get_all_stocks(db)
        for stock in stocks:
            change_percent = random.uniform(-0.02, 0.02)
            new_price = round(stock.current_price * (1 + change_percent), 2)

            stock.current_price = new_price
            stock.day_high = max(stock.day_high or new_price, new_price)
            stock.day_low = min(stock.day_low or new_price, new_price)
            stock.volume += random.randint(1000, 100000)
            stock.updated_at = datetime.utcnow()

        db.commit()
        return stocks

    @staticmethod
    def get_stock_price(db: Session, symbol: str) -> Optional[float]:
        """Get current price for a stock."""
        stock = MarketService.get_stock(db, symbol)
        return stock.current_price if stock else None

    @staticmethod
    def calculate_change(stock: Stock) -> tuple:
        """Calculate price change and percentage from previous close."""
        if stock.previous_close and stock.previous_close > 0:
            change = round(stock.current_price - stock.previous_close, 2)
            change_percent = round((change / stock.previous_close) * 100, 2)
            return change, change_percent
        return 0.0, 0.0
