# File: .\craps\strategies\free_odds_strategy.py

from craps.rules_engine import RulesEngine  # Import RulesEngine

class FreeOddsStrategy:
    """Betting strategy for Free Odds on any active bet."""
    def __init__(self, table, odds_multiple="1x"):
        """
        Initialize the Free Odds strategy.
        
        :param table: The table object to determine minimum bets.
        :param odds_multiple: The odds multiple (e.g., "1x", "2x", "3x", "1-2-3", "3-4-5").
        """
        self.table = table
        self.odds_multiple = odds_multiple
        self.rules_engine = RulesEngine()  # Initialize RulesEngine

    def get_odds_amount(self, original_bet_amount):
        """Calculate the odds amount based on the original bet amount and the selected multiple."""
        if self.odds_multiple == "1x":
            return original_bet_amount
        elif self.odds_multiple == "2x":
            return original_bet_amount * 2
        elif self.odds_multiple == "3x":
            return original_bet_amount * 3
        elif self.odds_multiple == "1-2-3":
            # 1x on 4/10, 2x on 5/9, 3x on 6/8
            return original_bet_amount
        elif self.odds_multiple == "3-4-5":
            # 3x on 4/10, 4x on 5/9, 5x on 6/8
            return original_bet_amount
        else:
            raise ValueError(f"Invalid odds multiple: {self.odds_multiple}")

    def get_bet(self, game_state, player):
        """Place Free Odds bets on any active bets."""
        bets = []

        for active_bet in player.active_bets:
            if active_bet.bet_type in ["Pass Line", "Place"]:
                # Calculate the odds amount based on the original bet amount
                odds_amount = self.get_odds_amount(active_bet.amount)

                # Create a Free Odds bet using RulesEngine
                if active_bet.bet_type == "Pass Line":
                    bets.append(self.rules_engine.create_bet(
                        "Pass Line Odds",
                        odds_amount,
                        player,
                        parent_bet=active_bet
                    ))
                elif active_bet.bet_type == "Place":
                    bets.append(self.rules_engine.create_bet(
                        "Place Odds",
                        odds_amount,
                        player,
                        number=active_bet.number,
                        parent_bet=active_bet
                    ))

        return bets if bets else None