from typing import Optional
from fastapi import APIRouter, Request, FastAPI
from craps.craps_engine import CrapsEngine
from craps.house_rules import HouseRules
from craps.api.api_session_manager import CrapsSession, session_manager
from craps.api.house_rules_api import router as house_rules_router

router = APIRouter(prefix="/api/session", tags=["Session Control"])

def start_new_session(rules: Optional[HouseRules] = None) -> CrapsSession:
    if rules is None:
        rules = HouseRules({})

    engine = CrapsEngine(quiet_mode=True)
    engine.setup_session(
        house_rules_dict=rules.to_dict(),
        num_shooters=rules.number_of_shooters,
        dice_mode=rules.dice_mode
    )

    session = CrapsSession(rules)
    session.engine = engine
    return session

@router.post("/start")
def start_session(request: Request) -> dict:
    session = start_new_session()
    session_id = session_manager.create_session(session.rules)
    session_manager.sessions[session_id] = session

    return {
        "session_id": session_id,
        "initial_state": {
            "point": session.engine.game_state.point if session.engine and session.engine.game_state else None,
            "puck": session.engine.game_state.puck_on if session.engine and session.engine.game_state else False,
            "bankrolls": {},
            "bets": [],
            "shooter_index": 0
        }
    }

app = FastAPI(title="Craps Simulator API")
app.include_router(house_rules_router)
app.include_router(router)
