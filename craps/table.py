# File: .\craps\table.py

from typing import List, Optional
from craps.bet import Bet
from craps.play_by_play import PlayByPlay
from craps.house_rules import HouseRules

class Table:
    def __init__(self, house_rules: HouseRules, play_by_play: PlayByPlay):
        """
        Initialize the table.

        :param house_rules: The HouseRules object for payout rules and limits.
        """
        self.house_rules = house_rules
        self.bets = []  # All bets on the table
        self.unit = self.house_rules.table_minimum // 5  # Unit for Place/Buy bets
        self.play_by_play = play_by_play

    def get_minimum_bet(self, number: int) -> int:
        """
        Get the minimum bet amount for a specific number.

        :param number: The number being bet on (e.g., 4, 5, 6, 8, 9, 10).
        :return: The minimum bet amount for the number.
        """
        if number in [6, 8]:
            # For 6 and 8, the minimum bet is 6 units (e.g., $6 if table minimum is $5)
            return self.house_rules.table_minimum + self.unit
        elif number in [4, 5, 9, 10]:
            # For other numbers, the minimum bet is the table minimum
            return self.house_rules.table_minimum
        else:
            raise ValueError(f"Invalid number for Place Bet: {number}")
    
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
            #self.play_by_play.write(message)
            return False

        # Place the bet on the table
        self.bets.append(bet)
        message = f"Bet placed: {bet}"
        #self.play_by_play.write(message)
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
            message = f"Bet resolved: {bet} (Status: {bet.status})"
            self.play_by_play.write(message)

    def clear_resolved_bets(self) -> List[Bet]:
        """
        Remove all resolved bets (won or lost) from the table and return them.

        :return: A list of resolved bets.
        """
        resolved_bets = [bet for bet in self.bets if bet.is_resolved()]
        self.bets = [bet for bet in self.bets if not bet.is_resolved()]
        message = f"Active bets after clearing resolved bets: {len(self.bets)}"
        #self.play_by_play.write(message)
        return resolved_bets