from typing import Dict, Optional, List
from fastapi import Request, HTTPException
from craps.house_rules import HouseRules
from craps.craps_engine import CrapsEngine
from craps.player import Player

class CrapsSession:
    def __init__(self, rules: HouseRules) -> None:
        self.rules = rules
        self.engine: Optional[CrapsEngine] = None
        self.players: List[Player] = []

class SessionManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, CrapsSession] = {}

    def create_session(self, rules: HouseRules) -> str:
        import uuid
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = CrapsSession(rules)
        return session_id

session_manager = SessionManager()

def get_session_by_request(request: Request) -> CrapsSession:
    session_key = request.headers.get("X-Session-Key")
    if not session_key or session_key not in session_manager.sessions:
        raise HTTPException(status_code=400, detail="Invalid or missing session key")
    return session_manager.sessions[session_key]
