# File: .\craps\bets\pass_line_odds.py

from craps.bets import Bet  # Import the base Bet class

class PassLineOddsBet(Bet):
    """Class representing a Pass Line Odds bet."""
    def __init__(self, amount, owner):
        super().__init__("Pass Line Odds", amount, owner, payout_ratio=(1, 1), locked=False)

    def resolve(self, outcome, game_state):
        """Resolve the Pass Line Odds bet based on the dice outcome and game state."""
        total = sum(outcome)
        
        if game_state.phase == "point":
            if total == game_state.point:
                # Determine the payout ratio based on the point
                if game_state.point in [4, 10]:
                    self.payout_ratio = (2, 1)  # 2:1 payout for 4 and 10
                elif game_state.point in [5, 9]:
                    self.payout_ratio = (3, 2)  # 3:2 payout for 5 and 9
                elif game_state.point in [6, 8]:
                    self.payout_ratio = (6, 5)  # 6:5 payout for 6 and 8
                self.status = "won"  # Pass Line Odds bet wins
                #print(f"{self.owner}'s ${self.amount} {self.bet_type} bet WON! Payout: ${self.payout()}.")
            elif total == 7:
                self.status = "lost"  # Pass Line Odds bet loses
                #print(f"{self.owner}'s ${self.amount} {self.bet_type} bet LOST (7-out).")
            else:
                # Bet remains active
                self.status = "active"
                #print(f"{self.owner}'s ${self.amount} {self.bet_type} bet remains ACTIVE (rolled {total}).")