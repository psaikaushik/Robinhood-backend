from routers.auth import router as auth_router
from routers.stocks import router as stocks_router
from routers.trading import router as trading_router
from routers.portfolio import router as portfolio_router
from routers.watchlist import router as watchlist_router

__all__ = [
    "auth_router",
    "stocks_router",
    "trading_router",
    "portfolio_router",
    "watchlist_router"
]
