from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Literal, Any, Optional, List

from craps.api.api_session_manager import get_session_by_request, CrapsSession
from craps.craps_engine import CrapsEngine
from craps.table import Bet
from craps.player import Player

router = APIRouter(prefix="/api/game", tags=["Game Control"])

class GameRollRequest(BaseModel):
    dice: Optional[tuple[int, int]] = None
    mode: Literal["manual", "auto"] = "manual"

class PlaceBetsRequest(BaseModel):
    bets: List[dict] = []  # Placeholder for future interactive bets

@router.post("/start")
def start_game(request: Request) -> dict[str, Any]:
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

@router.post("/reset")
def reset_game(request: Request) -> dict[str, Any]:
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

@router.post("/roll")
def roll_dice(request: Request, body: GameRollRequest) -> dict[str, Any]:
    session: CrapsSession = get_session_by_request(request)
    engine = session.engine

    if not engine:
        raise HTTPException(status_code=400, detail="Game has not been started")

    if engine.stats and engine.shooter_index >= engine.stats.num_shooters:
        raise HTTPException(status_code=400, detail="Game is over")

    # Determine previous phase before rolling
    previous_phase = engine.game_state.phase if engine.game_state else "come-out"

    # Manual or engine-based dice roll
    roll = body.dice if body.dice else engine.roll_dice()

    # Resolve roll
    engine.resolve_bets(roll)
    engine.refresh_bet_statuses()
    summary = engine.handle_post_roll(roll, previous_phase)
    engine.log_player_bets()

    response = _snapshot_game_state(engine)
    response.update({
        "roll": roll,
        "roll_number": engine.stats.session_rolls if engine.stats else 0,
        "summary": summary._asdict()
    })
    return response

@router.post("/bets/place")
def place_bets(request: Request, body: PlaceBetsRequest) -> dict[str, Any]:
    session: CrapsSession = get_session_by_request(request)
    engine = session.engine

    if not engine:
        raise HTTPException(status_code=400, detail="Game has not been started")

    # TODO: Process body.bets for interactive players (currently unused)
    engine.lock_session()
    engine.accept_bets()


    return _snapshot_game_state(engine)

@router.post("/bets/adjust")
def adjust_bets(request: Request) -> dict[str, Any]:
    session: CrapsSession = get_session_by_request(request)
    engine = session.engine

    if not engine:
        raise HTTPException(status_code=400, detail="Game has not been started")

    # TODO: In the future, process manual bet adjustments from interactive player
    engine.adjust_bets()

    return _snapshot_game_state(engine)

@router.get("/status")
def get_game_status(request: Request) -> dict[str, Any]:
    session: CrapsSession = get_session_by_request(request)
    engine = session.engine

    if not engine:
        raise HTTPException(status_code=400, detail="Game has not been started")

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
