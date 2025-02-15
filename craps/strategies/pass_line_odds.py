# File: craps/strategies/pass_line_odds.py
from craps.bet_factory import BetFactory

class PassLineOddsStrategy:
    """Betting strategy for Pass Line with Odds bets."""
    def __init__(self, table, odds_multiple=1):
        """
        Initialize the Pass Line Odds strategy.
        
        :param table: The table object to determine minimum bets.
        :param odds_multiple: The multiple of the minimum bet to use for odds (e.g., 1x, 2x).
        """
        self.table = table
        self.odds_multiple = odds_multiple

    def get_bet(self, game_state, player):
        """Place a Pass Line or Pass Line Odds bet based on the game state."""
        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if any(b.bet_type == "Pass Line" for b in player.active_bets):
                return None  # No new bet to place

            # Use the BetFactory to create a Pass Line bet
            return BetFactory.create_pass_line_bet(self.table.house_rules.table_minimum, player.name)
        
        elif game_state.phase == "point":
            # Check if the player already has an active Pass Line Odds bet
            if any(b.bet_type.startswith("Place Odds") for b in player.active_bets):
                return None  # No new bet to place

            # Use the BetFactory to create a Place Odds bet on the point number
            return BetFactory.create_place_odds_bet(
                self.table.house_rules.table_minimum * self.odds_multiple,  # Bet amount
                player.name,  # Owner
                game_state.point  # Point number
            )
        
        return None  # No bet to place