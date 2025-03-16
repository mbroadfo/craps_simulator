from typing import List, Any
from config import ACTIVE_PLAYERS
from craps.player import Player
from craps.house_rules import HouseRules
from craps.table import Table

class SetupPlayers:
    """
    Responsible for setting up players with names, bankroll, and strategies.
    This was previously handled in SingleSession.
    """

    def __init__(self, house_rules: HouseRules, table: Table, strategies: List[Any], initial_bankroll: int = 500):
        """
        Initialize player setup.

        :param house_rules: The HouseRules instance to enforce table limits.
        :param table: The game table where players will place bets.
        :param strategies: List of betting strategies, one per player.
        :param initial_bankroll: Starting bankroll for each player.
        """
        self.house_rules = house_rules
        self.table = table
        self.strategies = strategies or []  # ✅ Ensure it's never None
        self.initial_bankroll = initial_bankroll

    def setup(self) -> List[Player]:
        """
        Create players and assign betting strategies.

        :return: A list of Player objects.
        """
        if not self.strategies:
            raise ValueError("No betting strategies provided. Cannot create players.")

        # ✅ Ensure player names align with strategy count
        num_players = len(self.strategies)
        if isinstance(ACTIVE_PLAYERS, list) and len(ACTIVE_PLAYERS) >= num_players:
            player_names = ACTIVE_PLAYERS[:num_players]
        else:
            player_names = [f"Player {i+1}" for i in range(num_players)]

        # ✅ Create Player instances
        players = [
            Player(name=player_names[i], initial_balance=self.initial_bankroll, betting_strategy=strategy)
            for i, strategy in enumerate(self.strategies)
        ]

        return players  # ✅ Now returns only the list of players
