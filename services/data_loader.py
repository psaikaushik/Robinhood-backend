import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from services.scenario import get_scenario_manager

# Default data directory
DATA_DIR = Path(__file__).parent.parent / "data"


class DataLoader:
    """Service for loading data from JSON files. Supports scenario-based data loading."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self._cache: Dict[str, Any] = {}

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load and cache JSON file. Checks scenario override first."""
        if filename not in self._cache:
            # Use scenario manager to get correct path
            scenario_mgr = get_scenario_manager()
            filepath = scenario_mgr.get_data_path(filename)

            if not filepath.exists():
                # Fall back to default data dir
                filepath = self.data_dir / filename

            if not filepath.exists():
                raise FileNotFoundError(f"Data file not found: {filepath}")

            with open(filepath, "r") as f:
                self._cache[filename] = json.load(f)
        return self._cache[filename]
        return self._cache[filename]

    def clear_cache(self):
        """Clear the data cache."""
        self._cache = {}

    def get_stocks(self) -> List[Dict[str, Any]]:
        """Load stock data from JSON."""
        data = self._load_json("stocks.json")
        return data.get("stocks", [])

    def get_stock(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get a specific stock by symbol."""
        stocks = self.get_stocks()
        for stock in stocks:
            if stock["symbol"].upper() == symbol.upper():
                return stock
        return None

    def get_users(self) -> List[Dict[str, Any]]:
        """Load user data from JSON."""
        data = self._load_json("users.json")
        return data.get("users", [])

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific user by ID."""
        users = self.get_users()
        for user in users:
            if user["id"] == user_id:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a specific user by username."""
        users = self.get_users()
        for user in users:
            if user["username"].lower() == username.lower():
                return user
        return None

    def get_holdings(self) -> List[Dict[str, Any]]:
        """Load holdings data from JSON."""
        data = self._load_json("holdings.json")
        return data.get("holdings", [])

    def get_user_holdings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get holdings for a specific user."""
        holdings = self.get_holdings()
        return [h for h in holdings if h["user_id"] == user_id]

    def get_orders(self) -> List[Dict[str, Any]]:
        """Load order data from JSON."""
        data = self._load_json("orders.json")
        return data.get("orders", [])

    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get orders for a specific user."""
        orders = self.get_orders()
        return [o for o in orders if o["user_id"] == user_id]

    def get_watchlists(self) -> List[Dict[str, Any]]:
        """Load watchlist data from JSON."""
        data = self._load_json("watchlists.json")
        return data.get("watchlists", [])

    def get_user_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """Get watchlist for a specific user."""
        watchlists = self.get_watchlists()
        return [w for w in watchlists if w["user_id"] == user_id]


# Global data loader instance
data_loader = DataLoader()


def get_data_loader() -> DataLoader:
    """Get the global data loader instance."""
    return data_loader
