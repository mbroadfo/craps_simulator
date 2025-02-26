# File: .\craps\table.py

from typing import List, Optional
from craps.bet import Bet
from craps.play_by_play import PlayByPlay
from craps.house_rules import HouseRules
from craps.rules_engine import RulesEngine

class Table:
    def __init__(self, house_rules, play_by_play, rules_engine):
        """
        Initialize the table.

        :param house_rules: The HouseRules object for payout rules and limits.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        :param rules_engine: The RulesEngine instance for resolving bets.
        """
        self.house_rules = house_rules
        self.bets = []  # All bets on the table
        self.unit = self.house_rules.table_minimum // 5  # Unit for Place/Buy bets
        self.play_by_play = play_by_play
        self.rules_engine = rules_engine

    def reactivate_inactive_bets(self):
        """
        Reactivate inactive Place bets when the point is set.
        """
        reactivated_bets = []
        for bet in self.bets:
            if bet.bet_type.startswith("Place") and bet.status == "inactive":
                bet.status = "active"
                reactivated_bets.append(f"{bet.owner.name}'s {bet.bet_type}")

        if reactivated_bets:
            message = f"{', '.join(reactivated_bets)} are now ON."
            self.play_by_play.write(message)

    def place_bet(self, bet: Bet, phase: str) -> bool:
        """
        Place a bet on the table after validating it.

        :param bet: The bet to place.
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet was placed successfully, False otherwise.
        """
        # Validate the bet before placing it
        if not bet.validate_bet(phase, self.house_rules.table_minimum, self.house_rules.table_maximum):
            message = f"Invalid bet: {bet}"
            self.play_by_play.write(message)
            return False

        # Place the bet on the table
        self.bets.append(bet)
        message = f"Bet placed: {bet}"
        self.play_by_play.write(message)
        return True

    def check_bets(self, dice_outcome: List[int], phase: str, point: Optional[int]) -> None:
        """
        Check and resolve all bets on the table based on the dice outcome, phase, and point.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        for bet in self.bets:
            bet.resolve(self.rules_engine, dice_outcome, phase, point)
            message = f"Bet resolved: {bet} (Status: {bet.status})"
            self.play_by_play.write(message)

    def clear_resolved_bets(self) -> List[Bet]:
        """
        Remove all resolved bets (won or lost) from the table and return them.
        """
        resolved_bets = [bet for bet in self.bets if bet.is_resolved()]
        self.bets = [bet for bet in self.bets if not bet.is_resolved()]
        return resolved_bets