# File: .\craps\strategies\pass_line.py

from craps.bet_factory import BetFactory

class PassLineStrategy:
    """Betting strategy for Pass Line bets."""
    def __init__(self, min_bet):
        self.min_bet = min_bet

    def get_bet(self, game_state, player):
        """Place a Pass Line bet during the come-out roll if no active bet exists."""
        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if any(b.bet_type == "Pass Line" for b in player.active_bets):
                return None  # No new bet to place

            # Use the BetFactory to create a Pass Line bet
            return BetFactory.create_pass_line_bet(self.min_bet, player.name)
        return None  # No bet to place