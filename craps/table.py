# File: craps/table.py

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
        self.unit = self.house_rules.table_minimum // 5 # Unit for Place bets

    def place_bet(self, bet: Bet) -> None:
        """
        Place a bet on the table.

        :param bet: The bet to place.
        :raises ValueError: If the bet amount is below the table minimum or above the table maximum.
        """
        if bet.amount < self.house_rules.table_minimum:
            raise ValueError(f"Bet amount ${bet.amount} is below the table minimum of ${self.house_rules.table_minimum}.")
        if bet.amount > self.house_rules.table_maximum:
            raise ValueError(f"Bet amount ${bet.amount} exceeds the table maximum of ${self.house_rules.table_maximum}.")
        self.bets.append(bet)
        logging.info(f"Bet placed: {bet}")

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

        # Remove resolved bets (won or lost) from the table
        self.bets = [bet for bet in self.bets if not bet.is_resolved()]
        logging.info(f"Active bets after resolution: {len(self.bets)}")

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