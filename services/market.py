import random
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from models.stock import Stock

# Simulated stock data - predefined stocks
MOCK_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "price": 178.50, "sector": "Technology", "market_cap": 2800000000000},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 141.25, "sector": "Technology", "market_cap": 1750000000000},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 378.90, "sector": "Technology", "market_cap": 2810000000000},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": 178.75, "sector": "Consumer Cyclical", "market_cap": 1850000000000},
    {"symbol": "TSLA", "name": "Tesla Inc.", "price": 248.50, "sector": "Automotive", "market_cap": 790000000000},
    {"symbol": "META", "name": "Meta Platforms Inc.", "price": 505.25, "sector": "Technology", "market_cap": 1300000000000},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 875.30, "sector": "Technology", "market_cap": 2160000000000},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "price": 198.45, "sector": "Financial Services", "market_cap": 570000000000},
    {"symbol": "V", "name": "Visa Inc.", "price": 279.80, "sector": "Financial Services", "market_cap": 575000000000},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "price": 156.30, "sector": "Healthcare", "market_cap": 375000000000},
    {"symbol": "WMT", "name": "Walmart Inc.", "price": 165.20, "sector": "Consumer Defensive", "market_cap": 445000000000},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "price": 158.75, "sector": "Consumer Defensive", "market_cap": 375000000000},
    {"symbol": "DIS", "name": "The Walt Disney Company", "price": 112.40, "sector": "Communication Services", "market_cap": 205000000000},
    {"symbol": "NFLX", "name": "Netflix Inc.", "price": 628.50, "sector": "Communication Services", "market_cap": 275000000000},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "price": 178.90, "sector": "Technology", "market_cap": 290000000000},
]


class MarketService:
    @staticmethod
    def initialize_stocks(db: Session) -> None:
        """Initialize the database with mock stock data."""
        for stock_data in MOCK_STOCKS:
            existing = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()
            if not existing:
                stock = Stock(
                    symbol=stock_data["symbol"],
                    name=stock_data["name"],
                    current_price=stock_data["price"],
                    previous_close=stock_data["price"],
                    day_high=stock_data["price"],
                    day_low=stock_data["price"],
                    volume=random.randint(1000000, 50000000),
                    market_cap=stock_data["market_cap"],
                    sector=stock_data["sector"]
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
