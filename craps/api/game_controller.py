from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Literal, Any

from craps.api.api_session_manager import get_session_by_request, CrapsSession
from craps.craps_engine import CrapsEngine
from craps.table import Bet
from craps.player import Player

router = APIRouter(prefix="/api/game", tags=["Game Control"])

class GameStartRequest(BaseModel):
    mode: Literal["manual", "auto"] = "auto"

@router.post("/start")
def start_game(request: Request, body: GameStartRequest) -> dict[str, Any]:
    session: CrapsSession = get_session_by_request(request)

    if not session.players:
        raise HTTPException(status_code=400, detail="No active players in session")

    engine = CrapsEngine(quiet_mode=True)
    session.engine = engine

    engine.setup_session(
        house_rules_dict=session.rules.__dict__,
        num_shooters=session.rules.number_of_shooters,
        num_players=len(session.players),
        dice_mode=session.rules.dice_mode
    )

    if engine.player_lineup is not None:
        engine.player_lineup.assign_strategies(session.players)

    if engine.stats is not None:
        engine.stats.initialize_player_stats(session.players)
        engine.stats.num_players = len(session.players)

    engine.assign_next_shooter()

    return _snapshot_game_state(engine)

def _snapshot_game_state(engine: CrapsEngine) -> dict[str, Any]:
    if not engine.game_state or not engine.table:
        raise HTTPException(status_code=500, detail="Game state is not initialized")

    active_players = engine.player_lineup.get_active_players_list() if engine.player_lineup else []

    return {
        "puck": engine.game_state.puck_on,
        "point": engine.game_state.point,
        "shooter_index": engine.shooter_index,
        "bankrolls": {p.name: p.balance for p in active_players},
        "bets": [
            b.serialize() if hasattr(b, "serialize") else {
                "owner": b.owner.name,
                "type": b.bet_type,
                "amount": b.amount,
                "status": b.status
            } for b in engine.table.bets
        ]
    }
