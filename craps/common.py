from typing import Optional, List, Tuple
from craps.house_rules import HouseRules
from craps.table import Table
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.player import Player
from craps.dice import Dice
from craps.statistics import Statistics
from craps.bet import Bet

class CommonTableSetup:
    """Common setup for all craps tests."""

    def __init__(self) -> None:
        """Initialize the table, players, and other components for testing."""
        # Initialize house rules
        self.house_rules_config: dict[str, int] = {
            "table_minimum": 10,  # Minimum bet amount
            "table_maximum": 5000,  # Maximum bet amount
        }
        self.house_rules: HouseRules = HouseRules(self.house_rules_config)

        # Initialize play-by-play and rules engine
        self.play_by_play: PlayByPlay = PlayByPlay()
        self.rules_engine: RulesEngine = RulesEngine()

        # Initialize the table
        self.table: Table = Table(self.house_rules, self.play_by_play)

        # Initialize a player
        self.player_name: str = "Alice"
        self.initial_balance: int = 1000
        self.player: Player = Player(self.player_name, self.initial_balance)

        # Initialize statistics
        self.stats: Statistics = Statistics(self.house_rules.table_minimum, num_shooters=10, num_players=1)

        # Initialize dice (optional, for testing specific rolls)
        self.dice: Dice = Dice()

    def place_bet(self, bet_type: str, amount: int, phase: str = "come-out", number: Optional[int] = None) -> Bet:
        """
        Place a bet on the table for the player.

        :param bet_type: The type of bet (e.g., "Field", "Pass Line").
        :param amount: The amount of the bet.
        :param phase: The current game phase ("come-out" or "point").
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :return: The created bet.
        """
        if bet_type == "Come Odds":
            # Ensure the Come bet has a number before placing the Come Odds bet
            come_bet: Optional[Bet] = next(
                (bet for bet in self.table.bets if bet.bet_type == "Come" and bet.owner == self.player), None
            )
            if come_bet is None or come_bet.number is None:
                raise ValueError("Cannot place Come Odds bet without an active Come bet with a number.")
            number = come_bet.number  # Use the number from the Come bet

        bet: Bet = self.rules_engine.create_bet(bet_type, amount, self.player, number=number)
        self.table.place_bet(bet, phase)
        return bet

    def simulate_roll(self, dice_outcome: Tuple[int, int], phase: str = "come-out", point: Optional[int] = None) -> List[Bet]:
        """
        Simulate a dice roll and resolve bets on the table.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        :return: A list of resolved bets.
        """
        self.table.check_bets(dice_outcome, phase, point)
        return self.table.clear_resolved_bets()

    def reset_table(self) -> None:
        """Reset the table and player for a new test."""
        self.table.bets = []  # Clear all bets
        self.player.balance = self.initial_balance  # Reset player balance
