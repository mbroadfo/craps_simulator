from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from collections.abc import AsyncIterator

from craps.api.house_rules_api import router as house_rules_router
from craps.api.api_session_controller import router as session_router
from craps.api.players_api import router as players_router
from craps.api.game_controller import router as game_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"📡 {route.path} {route.methods}")
    yield  # startup complete
    # shutdown logic can go here later

app = FastAPI(title="Craps Simulator API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(house_rules_router)
app.include_router(session_router)
app.include_router(players_router)
app.include_router(game_router)
