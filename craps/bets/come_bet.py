# File: .\craps\bets\come_bet.py

from craps.bet import Bet
from typing import Optional, List

class ComeBet(Bet):
    def __init__(self, amount: int, owner):
        """
        Initialize a Come bet.

        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        """
        super().__init__(
            bet_type="Come",
            amount=amount,
            owner=owner,
            payout_ratio=(1, 1),  # Come bets pay 1:1
            locked=False,  # Come bets can be taken down
            valid_phases=["come-out"],  # Come bets are placed during the come-out phase
        )
        self.come_point = None  # The point number for the Come bet (set after moving to the point)

    def resolve(self, outcome: List[int], phase: str, point: Optional[int]):
        """
        Resolve the Come bet based on the dice outcome, phase, and point.

        :param outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        total = sum(outcome)

        if self.come_point is None:
            # Come bet is still in the come-out phase
            if total in [7, 11]:
                self.status = "won"  # Come bet wins
            elif total in [2, 3, 12]:
                self.status = "lost"  # Come bet loses
            else:
                # Move the Come bet to the point
                self.bet_type="Come" + " " + str(total),
                self.come_point = total
                self.valid_phases = ["point"]  # Now only valid during the point phase
                self.status = "active"  # Bet remains active
        else:
            # Come bet has a point
            if total == self.come_point:
                self.status = "won"  # Come bet wins
            elif total == 7:
                self.status = "lost"  # Come bet loses
            else:
                self.status = "active"  # Bet remains active