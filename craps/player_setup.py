from config import ACTIVE_PLAYERS
from craps.player import Player
from typing import List

class SetupPlayers:
    def __init__(self) -> None:  # ✅ Explicit return type annotation
        """Initialize player setup."""
        self.active_players: dict[str, bool] = ACTIVE_PLAYERS  # ✅ Typed dictionary

    def setup(self) -> List[Player]:  # ✅ Now fully type hinted
        """Create and return a list of active players based on ACTIVE_PLAYERS settings."""
        players: List[Player] = [
            Player(name=strategy, initial_balance=500, betting_strategy=strategy)
            for strategy, enabled in self.active_players.items() if enabled  # ✅ Only include enabled strategies
        ]

        if not players:
            raise ValueError("No active players found. Cannot start session.")

        return players
