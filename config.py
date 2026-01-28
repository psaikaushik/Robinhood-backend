import os

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./robinhood.db")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initial balance for new users
INITIAL_BALANCE = 10000.00
