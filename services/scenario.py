"""
Chaos Engineering Scenario Loader

This module allows interviewers to switch between different scenarios
to test candidates on edge cases, data issues, and system resilience.

Usage:
    Set SCENARIO environment variable before starting the server:

    # Default clean scenario
    SCENARIO=default python main.py

    # Chaos data scenario
    SCENARIO=chaos_data python main.py

    # Stress test scenario
    SCENARIO=chaos_stress python main.py
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


class ScenarioManager:
    """Manages chaos engineering scenarios for interviews."""

    _instance = None
    _current_scenario: Optional[str] = None
    _scenario_config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._current_scenario is None:
            self.load_scenario(os.getenv("SCENARIO", "default"))

    def load_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Load a scenario by ID."""
        scenario_path = SCENARIOS_DIR / scenario_id / "config.json"

        if not scenario_path.exists():
            print(f"⚠️  Scenario '{scenario_id}' not found, using default")
            scenario_id = "default"
            scenario_path = SCENARIOS_DIR / scenario_id / "config.json"

        if scenario_path.exists():
            with open(scenario_path) as f:
                self._scenario_config = json.load(f)
        else:
            self._scenario_config = {
                "id": "default",
                "name": "Default",
                "description": "Normal operation",
                "challenges": []
            }

        self._current_scenario = scenario_id
        print(f"📋 Loaded scenario: {self._scenario_config.get('name', scenario_id)}")

        return self._scenario_config

    @property
    def current_scenario(self) -> str:
        return self._current_scenario or "default"

    @property
    def config(self) -> Dict[str, Any]:
        return self._scenario_config or {}

    def get_data_path(self, filename: str) -> Path:
        """Get the path to a data file, checking scenario override first."""
        # Check if scenario has custom data file
        scenario_data = SCENARIOS_DIR / self.current_scenario / filename
        if scenario_data.exists():
            return scenario_data

        # Fall back to default data
        return DEFAULT_DATA_DIR / filename

    def get_scenario_info(self) -> Dict[str, Any]:
        """Get current scenario information."""
        return {
            "scenario_id": self.current_scenario,
            "name": self.config.get("name", "Unknown"),
            "description": self.config.get("description", ""),
            "difficulty": self.config.get("difficulty", "unknown"),
            "challenges": self.config.get("challenges", []),
            "setup": self.config.get("setup", {})
        }

    def get_setup(self) -> Dict[str, Any]:
        """Get scenario setup configuration."""
        return self.config.get("setup", {})

    def should_pre_populate_alerts(self) -> bool:
        """Check if scenario requires pre-populating alerts."""
        setup = self.get_setup()
        return setup.get("pre_populate_alerts", 0) > 0

    def get_pre_populate_alert_count(self) -> int:
        """Get number of alerts to pre-populate."""
        setup = self.get_setup()
        return setup.get("pre_populate_alerts", 0)

    def get_artificial_delay_ms(self) -> int:
        """Get artificial delay in milliseconds (for race condition testing)."""
        setup = self.get_setup()
        return setup.get("artificial_delay_ms", 0)

    def is_concurrent_test_enabled(self) -> bool:
        """Check if concurrent test endpoint should be enabled."""
        setup = self.get_setup()
        return setup.get("enable_concurrent_test_endpoint", False)

    @classmethod
    def list_scenarios(cls) -> List[Dict[str, Any]]:
        """List all available scenarios."""
        scenarios = []
        if SCENARIOS_DIR.exists():
            for scenario_dir in SCENARIOS_DIR.iterdir():
                if scenario_dir.is_dir():
                    config_path = scenario_dir / "config.json"
                    if config_path.exists():
                        with open(config_path) as f:
                            config = json.load(f)
                            scenarios.append({
                                "id": config.get("id", scenario_dir.name),
                                "name": config.get("name", scenario_dir.name),
                                "description": config.get("description", ""),
                                "difficulty": config.get("difficulty", "unknown")
                            })
        return scenarios


# Global instance
scenario_manager = ScenarioManager()


def get_scenario_manager() -> ScenarioManager:
    """Get the global scenario manager instance."""
    return scenario_manager
