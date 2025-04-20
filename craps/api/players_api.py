from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Any

from craps.api.api_session_manager import get_session_by_request, CrapsSession
from config import ACTIVE_PLAYERS
from craps.player import Player  # TODO: Replace with strategy instantiation

router = APIRouter(prefix="/api/players", tags=["Players"])

class PlayerPatchRequest(BaseModel):
    name: str
    active: bool

@router.get("/")
def get_all_players(request: Request) -> List[dict[str, Any]]:
    session: CrapsSession = get_session_by_request(request)

    # If no players in session, load active ones from config
    if not session.players:
        for name, (strategy, is_active) in ACTIVE_PLAYERS.items():
            if is_active:
                session.players.append(Player(name=name))

    active_names = {p.name for p in session.players}

    result = []
    for name, (strategy, _) in ACTIVE_PLAYERS.items():
        result.append({
            "name": name,
            "strategy": strategy,
            "active": name in active_names
        })
    return result

@router.patch("/")
def patch_players(request: Request, updates: List[PlayerPatchRequest]) -> dict[str, str]:
    session: CrapsSession = get_session_by_request(request)

    # Remove deselected players
    session.players = [p for p in session.players if all(p.name != u.name or u.active for u in updates)]

    # Add newly activated players
    for update in updates:
        if update.active and not any(p.name == update.name for p in session.players):
            if update.name not in ACTIVE_PLAYERS:
                raise HTTPException(status_code=400, detail=f"Unknown player: {update.name}")
            session.players.append(Player(name=update.name))

    return {"status": "ok"}
