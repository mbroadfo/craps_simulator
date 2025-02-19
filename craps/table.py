# File: .\craps\table.py

from typing import List, Optional
from craps.bet import Bet
from craps.house_rules import HouseRules
import logging

class Table:
    def __init__(self, house_rules: HouseRules):
        """
        Initialize the table.

        :param house_rules: The HouseRules object for payout rules and limits.
        """
        self.house_rules = house_rules
        self.bets = []  # Start with no bets on the table
        self.unit = self.house_rules.table_minimum // 5  # Unit for Place bets

    def place_bet(self, bet: Bet, phase: str) -> bool:
        """
        Place a bet on the table after validating it.

        :param bet: The bet to place.
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet was placed successfully, False otherwise.
        """
        # Validate the bet before placing it
        if not bet.validate_bet(phase, self.house_rules.table_minimum, self.house_rules.table_maximum):
            logging.warning(f"Invalid bet: {bet}")
            return False

        # Place the bet on the table
        self.bets.append(bet)
        logging.info(f"Bet placed: {bet}")
        return True

    def check_bets(self, dice_outcome: List[int], phase: str, point: Optional[int]) -> None:
        """
        Check and resolve all bets on the table based on the dice outcome, phase, and point.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        for bet in self.bets:
            bet.resolve(dice_outcome, phase, point)
            logging.info(f"Bet resolved: {bet} (Status: {bet.status})")

    def clear_resolved_bets(self) -> None:
        """
        Remove all resolved bets (won or lost) from the table.
        """
        # Keep only active bets
        self.bets = [bet for bet in self.bets if not bet.is_resolved()]
        logging.info(f"Active bets after clearing resolved bets: {len(self.bets)}")

    def get_minimum_bet(self, number: int) -> int:
        """
        Get the minimum bet for a Place bet on a specific number.

        :param number: The number being bet on (4, 5, 6, 8, 9, or 10).
        :return: The minimum bet amount.
        """
        if number in [6, 8]:
            # For 6 and 8, the minimum bet is table minimum + unit
            return self.house_rules.table_minimum + self.unit
        else:
            # For other numbers, the minimum bet is the table minimum
            return self.house_rules.table_minimum