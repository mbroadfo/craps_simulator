from typing import Dict, Optional
from fastapi import Request, HTTPException
from craps.house_rules import HouseRules
from craps.craps_engine import CrapsEngine

class CrapsSession:
    def __init__(self, rules: HouseRules) -> None:
        self.rules = rules
        self.engine: Optional[CrapsEngine] = None

class SessionManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, CrapsSession] = {}

    def create_session(self, rules: HouseRules) -> str:
        import uuid
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = CrapsSession(rules)
        return session_id

    def get_session(self, session_id: str) -> CrapsSession:
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Invalid session ID")
        return self.sessions[session_id]

session_manager = SessionManager()

def get_session_by_request(request: Request) -> CrapsSession:
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    return session_manager.get_session(session_id)