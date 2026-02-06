"""Admin endpoints for runtime chaos control."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from services.database import get_db
from services.chaos_runtime import ChaosRuntime

router = APIRouter()


class ChaosRequest(BaseModel):
    scenario: str  # chaos_data, chaos_stress, chaos_race


class ChaosStatusResponse(BaseModel):
    active: Optional[str]
    available: list[str]


AVAILABLE_SCENARIOS = ["chaos_data", "chaos_stress", "chaos_race"]


@router.get("/chaos/status", response_model=ChaosStatusResponse)
async def get_chaos_status():
    """Get current chaos status."""
    return ChaosStatusResponse(
        active=ChaosRuntime.get_active_scenario(),
        available=AVAILABLE_SCENARIOS
    )


@router.post("/chaos/activate")
async def activate_chaos(
    request: ChaosRequest,
    db: Session = Depends(get_db)
):
    """Activate a chaos scenario at runtime."""

    if request.scenario not in AVAILABLE_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Available: {AVAILABLE_SCENARIOS}"
        )

    try:
        result = ChaosRuntime.activate(db, request.scenario)
        return {
            "message": f"Chaos scenario '{request.scenario}' activated",
            "scenario": request.scenario,
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate chaos: {str(e)}"
        )


@router.post("/chaos/reset")
async def reset_chaos(db: Session = Depends(get_db)):
    """Reset to clean state."""

    try:
        result = ChaosRuntime.reset(db)
        return {
            "message": "Chaos reset to clean state",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset chaos: {str(e)}"
        )
