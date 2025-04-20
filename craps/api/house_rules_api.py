from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Any
from pydantic import BaseModel

from craps.api.api_session_manager import get_session_by_request
from craps.house_rules import HouseRules

router = APIRouter(prefix="/api/house_rules", tags=["House Rules"])


class HouseRulesUpdate(BaseModel):
    number_of_shooters: int | None = None
    dice_mode: str | None = None
    field_bet_payout_2: int | None = None
    field_bet_payout_12: int | None = None
    table_minimum: int | None = None
    table_maximum: int | None = None
    come_odds_working_on_come_out: bool | None = None
    vig_on_win: bool | None = None
    leave_winning_bets_up: bool | None = None
    leave_bets_working: bool | None = None


@router.get("/")
def get_house_rules(request: Request) -> dict[str, Any]:
    session = get_session_by_request(request)
    return session.rules.to_dict()


@router.post("/")
def set_house_rules(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    session = get_session_by_request(request)
    session.rules = HouseRules(body)
    return {"status": "updated", "rules": session.rules.to_dict()}


@router.patch("/")
def patch_house_rules(request: Request, updates: HouseRulesUpdate) -> dict[str, Any]:
    session = get_session_by_request(request)
    for key, value in updates.model_dump(exclude_unset=True).items():
        if hasattr(session.rules, key):
            setattr(session.rules, key, value)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown rule: {key}")
    return {"status": "patched", "rules": session.rules.to_dict()}
