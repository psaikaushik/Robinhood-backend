from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, SessionLocal
from routers import auth_router, stocks_router, trading_router, portfolio_router, watchlist_router, price_alerts_router
from services.market import MarketService

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Robinhood Clone API",
    description="A lightweight Robinhood-style trading platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(trading_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(price_alerts_router)


@app.on_event("startup")
def startup_event():
    """Initialize database with mock stock data on startup."""
    db = SessionLocal()
    try:
        MarketService.initialize_stocks(db)
    finally:
        db.close()


@app.get("/", tags=["Root"])
def root():
    """API root endpoint."""
    return {
        "message": "Welcome to Robinhood Clone API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "stocks": "/stocks",
            "orders": "/orders",
            "portfolio": "/portfolio",
            "watchlist": "/watchlist",
            "alerts": "/alerts"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
