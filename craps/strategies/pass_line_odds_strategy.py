# File: .\craps\strategies\pass_line_odds.py

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

    def get_bet(self, game_state, player, table):
        """Place a Pass Line or Pass Line Odds bet based on the game state."""
        if game_state.phase not in ["come-out", "point"]:
            return None  # Do not place the bet if the phase is invalid

        if game_state.phase == "come-out":
            # Check if the player already has an active Pass Line bet
            if player.has_active_bet(table, "Pass Line"):
                return None  # No new bet to place

            # Use the BetFactory to create a Pass Line bet
            return BetFactory.create_pass_line_bet(self.table.house_rules.table_minimum, player)
        
        elif game_state.phase == "point":
            # Check if the player already has an active Pass Line Odds bet
            if player.has_active_bet(table, "Pass Line Odds"):
                return None  # No new bet to place

            # Find the player's active Pass Line bet
            pass_line_bet = next(
                (bet for bet in table.bets if bet.owner == player and bet.bet_type == "Pass Line"),
                None
            )
            if pass_line_bet is None:
                return None  # No Pass Line bet found

            # Use the BetFactory to create a Pass Line Odds bet linked to the Pass Line bet
            return BetFactory.create_pass_line_odds_bet(
                self.table.house_rules.table_minimum * self.odds_multiple,  # Bet amount
                player,  # Owner
                pass_line_bet  # Parent Pass Line bet
            )
        
        return None  # No bet to place