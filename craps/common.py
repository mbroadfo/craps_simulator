# File: .\craps\common.py

from craps.house_rules import HouseRules
from craps.table import Table
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.player import Player
from craps.dice import Dice
from craps.statistics import Statistics  # Import the Statistics class

class CommonTableSetup:
    """Common setup for all craps tests."""

    def __init__(self):
        """Initialize the table, players, and other components for testing."""
        # Initialize house rules
        self.house_rules_config = {
            "table_minimum": 10,  # Minimum bet amount
            "table_maximum": 5000,  # Maximum bet amount
        }
        self.house_rules = HouseRules(self.house_rules_config)

        # Initialize play-by-play and rules engine
        self.play_by_play = PlayByPlay()
        self.rules_engine = RulesEngine()

        # Initialize the table
        self.table = Table(self.house_rules, self.play_by_play, self.rules_engine)

        # Initialize a player
        self.player_name = "Alice"
        self.initial_balance = 1000
        self.player = Player(self.player_name, self.initial_balance)

        # Initialize statistics
        self.stats = Statistics(self.house_rules.table_minimum, num_shooters=10, num_players=1)

        # Initialize dice (optional, for testing specific rolls)
        self.dice = Dice()

    def place_bet(self, bet_type, amount, phase="come-out", number=None):
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
            come_bet = next((bet for bet in self.table.bets if bet.bet_type == "Come" and bet.owner == self.player), None)
            if come_bet is None or come_bet.number is None:
                raise ValueError("Cannot place Come Odds bet without an active Come bet with a number.")
            number = come_bet.number  # Use the number from the Come bet

        bet = self.rules_engine.create_bet(bet_type, amount, self.player, number=number)
        self.table.place_bet(bet, phase)
        return bet

    def simulate_roll(self, dice_outcome, phase="come-out", point=None):
        """
        Simulate a dice roll and resolve bets on the table.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        :return: A list of resolved bets.
        """
        self.table.check_bets(dice_outcome, phase, point)
        return self.table.clear_resolved_bets()

    def reset_table(self):
        """Reset the table and player for a new test."""
        self.table.bets = []  # Clear all bets
        self.player.balance = self.initial_balance  # Reset player balance