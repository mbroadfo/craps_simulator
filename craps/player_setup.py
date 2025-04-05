from config import ACTIVE_PLAYERS
from craps.player import Player
from typing import List

class SetupPlayers:
    def __init__(self) -> None:
        """Initialize player setup."""
        self.active_players: dict[str, bool] = ACTIVE_PLAYERS

    def setup(self) -> List[Player]:
        """
        Create and return a list of active players based on ACTIVE_PLAYERS settings.
        Returns an empty list if none are active — caller should handle that case.
        """
        players: List[Player] = [
            Player(name=strategy, initial_balance=500)
            for strategy, enabled in self.active_players.items() if enabled
        ]

        return players
