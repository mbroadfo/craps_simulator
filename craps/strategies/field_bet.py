# File: craps/strategies/field_bet.py
from craps.bet_factory import BetFactory

class FieldBetStrategy:
    """Betting strategy for Field bets."""
    def __init__(self, min_bet):
        """
        Initialize the Field Bet strategy.
        
        :param min_bet: The minimum bet amount for the table.
        """
        self.min_bet = min_bet

    def get_bet(self, game_state, player):
        """Place a Field bet if no active Field bet exists."""
        # Check if the player already has an active Field bet
        if any(b.bet_type == "Field" for b in player.active_bets):
            return None  # No new bet to place

        # Use the BetFactory to create a Field bet
        return BetFactory.create_field_bet(self.min_bet, player.name)