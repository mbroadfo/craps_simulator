import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Optional, List, Tuple, Union
from config import HOUSE_RULES
from craps.house_rules import HouseRules
from craps.log_manager import LogManager
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.player import Player
from craps.bet import Bet
from craps.session_initializer import InitializeSession
from craps.lineup import PlayerLineup

class CommonTableSetup:
    """Common setup for all craps tests, now using InitializeSession for consistency."""

    def __init__(self) -> None:
        """Initialize the table, players, and other components for testing."""

        # ✅ Create instances for required objects
        house_rules = HouseRules(HOUSE_RULES)
        play_by_play = PlayByPlay()
        log_manager = LogManager()
        rules_engine = RulesEngine()
        player_lineup = PlayerLineup(house_rules, None, play_by_play, rules_engine)

        # ✅ Use these in InitializeSession
        session_initializer = InitializeSession(
            session_mode="live",
            house_rules=house_rules,
            play_by_play=play_by_play,
            log_manager=log_manager,
            rules_engine=rules_engine,
            player_lineup=player_lineup
        )

        session_data = session_initializer.prepare_session(num_shooters=10, num_players=1)

        if session_data is None:
            raise RuntimeError("Failed to initialize common test session.")

        self.house_rules, self.table, self.roll_history_manager, _, self.play_by_play, self.stats, self.game_state = session_data

        # ✅ Setup Player
        self.player_name = "Alice"
        self.initial_balance = 1000
        self.rules_engine = RulesEngine()
        self.player = Player(self.player_name, self.initial_balance)

        # ✅ Setup Gamestate
        self.game_state.set_table(self.table)

    def place_bet(self, bet_type: str, amount: int, phase: str = "come-out", number: Optional[Union[int, Tuple[int, int]]] = None) -> Bet:
        """
        Place a bet on the table for the player.

        :param bet_type: The type of bet (e.g., "Field", "Pass Line").
        :param amount: The amount of the bet.
        :param phase: The current game phase ("come-out" or "point").
        :param number: The number associated with the bet (e.g., 6 for Place 6 or (2,5) for Hop bets).
        :return: The created bet.
        """
        if bet_type == "Come Odds":
            come_bet = next(
                (bet for bet in self.table.bets if bet.bet_type == "Come" and bet.owner == self.player), None
            )
            if come_bet is None or come_bet.number is None:
                raise ValueError("Cannot place Come Odds bet without an active Come bet with a number.")
            number = come_bet.number

        bet = self.rules_engine.create_bet(bet_type, amount, self.player, number=number)
        self.table.place_bet(bet, phase)
        return bet

    def simulate_roll(self, dice_outcome: Tuple[int, int], phase: str = "come-out", point: Optional[int] = None) -> List[Bet]:
        """
        Simulate a dice roll and resolve bets on the table.

        :param dice_outcome: The result of the dice roll (e.g., (3, 4)).
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
