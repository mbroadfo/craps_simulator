from fastapi import FastAPI

from craps.api.house_rules_api import router as house_rules_router
from craps.api.api_session_controller import router as session_router
from craps.api.players_api import router as players_router

app = FastAPI(title="Craps Simulator API")

app.include_router(house_rules_router)
app.include_router(session_router)
app.include_router(players_router)
