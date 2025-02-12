# File: .\craps\bets\pass_line.py

from craps.bets import Bet  # Import the base Bet class

class PassLineBet(Bet):
    """Class representing a Pass Line bet."""
    def __init__(self, amount, owner):
        super().__init__("Pass Line", amount, owner, payout_ratio=(1, 1), locked=True)

    def resolve(self, outcome, game_state):
        """Resolve the Pass Line bet based on the dice outcome and game state."""
        total = sum(outcome)
        
        if game_state.phase == "come-out":
            # Come-out phase rules
            if total in [7, 11]:
                self.status = "won"  # Pass Line bet wins
            elif total in [2, 3, 12]:
                self.status = "lost"  # Pass Line bet loses
            else:
                # Point is set; bet remains active
                self.status = "active"
        else:  # Point phase
            if total == game_state.point:
                self.status = "won"  # Pass Line bet wins
            elif total == 7:
                self.status = "lost"  # Pass Line bet loses
            else:
                # Bet remains active
                self.status = "active"