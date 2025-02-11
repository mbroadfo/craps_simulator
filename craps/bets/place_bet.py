# File: .\craps\bets\place_bet.py

from ..bets import Bet  # Import the base Bet class

class PlaceBet(Bet):
    """Class representing a Place bet."""
    def __init__(self, amount, owner, number):
        """
        Initialize a Place bet.
        
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param number: The number being bet on (4, 5, 6, 8, 9, or 10).
        """
        super().__init__(f"Place {number}", amount, owner, locked=False)
        self.number = number

    def resolve(self, outcome, game_state):
        """Resolve the Place bet based on the dice outcome and game state."""
        total = sum(outcome)
        
        if game_state.phase == "come-out":
            # Place bets are inactive during the come-out phase
            self.status = "inactive"
            return
        
        # Only resolve Place bets during the point phase
        if game_state.phase == "point":
            if total == self.number:
                # Determine the payout ratio based on the number
                if self.number in [4, 10]:
                    self.payout_ratio = (9, 5)  # 9:5 payout for 4 and 10
                elif self.number in [5, 9]:
                    self.payout_ratio = (7, 5)  # 7:5 payout for 5 and 9
                elif self.number in [6, 8]:
                    self.payout_ratio = (7, 6)  # 7:6 payout for 6 and 8
                self.status = "won"  # Place bet wins
            elif total == 7:
                self.status = "lost"  # Place bet loses on 7-out
            else:
                # Bet remains active
                self.status = "active"