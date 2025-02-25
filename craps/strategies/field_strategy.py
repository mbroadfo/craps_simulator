# File: .\craps\strategies\field_strategy.py

from craps.rules_engine import RulesEngine  # Import RulesEngine

class FieldBetStrategy:
    """Betting strategy for Field bets."""
    def __init__(self, min_bet):
        """
        Initialize the Field Bet strategy.
        
        :param min_bet: The minimum bet amount for the table.
        """
        self.min_bet = min_bet
        self.rules_engine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state, player, table):
        """Place a Field bet during the point roll if no active bet exists."""
        if game_state.phase != "point":
            return None  # Only place bets after the point is established
        else:
            # Check if the player already has an active Field bet
            if player.has_active_bet(table, "Field"):
                return None  # No new bet to place

        # Use RulesEngine to create a Field bet
        return self.rules_engine.create_bet("Field", self.min_bet, player)