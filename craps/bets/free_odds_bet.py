# File: .\craps\bets\free_odds.py

from . import Bet

class FreeOddsBet(Bet):
    """Class representing a Free Odds bet (for Pass Line Odds or Place Bets)."""
    def __init__(self, bet_type, amount, owner, parent_bet):
        """
        Initialize a Free Odds bet.
        
        :param bet_type: The type of bet (e.g., "Pass Line Odds", "Place Odds").
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param parent_bet: The parent bet this odds bet is linked to.
        """
        if parent_bet is None:
            raise ValueError("FreeOddsBet requires a parent bet")
            
        super().__init__(
            bet_type=bet_type,
            amount=amount,
            owner=owner,
            payout_ratio=(1, 1),
            locked=False,
            valid_phases=["point"],
            number=parent_bet.number,  # Inherit number from parent
            parent_bet=parent_bet
        )

    def _calculate_true_odds(self, number):
        """Calculate the true odds payout ratio based on the number."""
        if number in [4, 10]:
            return (2, 1)  # 2:1 payout for 4 and 10
        elif number in [5, 9]:
            return (3, 2)  # 3:2 payout for 5 and 9
        elif number in [6, 8]:
            return (6, 5)  # 6:5 payout for 6 and 8
        else:
            raise ValueError(f"Invalid number for odds bet: {number}")
    
    def resolve(self, outcome, phase, point):
        """Resolve the Free Odds bet based on the dice outcome, phase, and point."""
        if phase not in self.valid_phases:
            return  # Do not resolve the bet if the phase is invalid

        total = sum(outcome)
        
        if phase == "point":
            if self.bet_type in ["Pass Line Odds", "Come Odds", "Place Odds"]:
                # Determine the number to resolve against
                if self.bet_type == "Pass Line Odds":
                    resolve_number = point
                else:
                    resolve_number = self.number

                # Resolve the bet
                if total == resolve_number:
                    self.payout_ratio = self._calculate_true_odds(resolve_number)
                    self.status = "won"  # Odds bet wins
                elif total == 7:
                    self.status = "lost"  # Odds bet loses
                else:
                    self.status = "active"  # Bet remains active
                    
    def payout(self) -> int:
        """
        Calculate the payout for the Free Odds bet.
        """
        if self.status != "won":
            return 0

        numerator, denominator = self.payout_ratio
        profit = (self.amount * numerator) // denominator  # Calculate profit
        return self.amount + profit  # Return total payout (original bet + profit)