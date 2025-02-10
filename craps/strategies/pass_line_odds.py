# File: .\craps\strategies\pass_line_odds.py

from craps.bets.pass_line import PassLineBet
from craps.bets.pass_line_odds import PassLineOddsBet

class PassLineOddsStrategy:
    """Betting strategy for Pass Line with Odds bets."""
    def __init__(self, min_bet, odds_multiple=1):
        self.min_bet = min_bet
        self.odds_multiple = odds_multiple

    def get_bet(self, game_state, player):
        """Place a Pass Line or Pass Line Odds bet based on the game state."""
        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if any(b.bet_type == "Pass Line" for b in player.active_bets):
                # print(f"{player.name} already has an active Pass Line bet.")
                return None  # No new bet to place

            # Place a new Pass Line bet
            return PassLineBet(self.min_bet, player.name)
        
        elif game_state.phase == "point":
            # Check if the player already has an active Pass Line Odds bet
            if any(b.bet_type == "Pass Line Odds" for b in player.active_bets):
                # print(f"{player.name} already has an active Pass Line Odds bet.")
                return None  # No new bet to place

            # Place a new Pass Line Odds bet
            return PassLineOddsBet(self.min_bet * self.odds_multiple, player.name)
        
        return None  # No bet to place