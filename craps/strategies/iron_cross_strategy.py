# File: .\craps\strategies\iron_cross.py

from craps.bet_factory import BetFactory
from craps.play_by_play import PlayByPlay

class IronCrossStrategy:
    """Betting strategy for Iron Cross."""
    def __init__(self, table, min_bet):
        """
        Initialize the Iron Cross strategy.
        
        :param table: The table object to determine minimum bets.
        :param min_bet: The minimum bet amount for the table.
        """
        self.table = table
        self.min_bet = min_bet

    def get_bet(self, game_state, player, table):
        """Place bets for the Iron Cross strategy."""
        if game_state.phase == "come-out":
            # Place a Pass Line bet during the come-out roll if no active bet exists
            if not any(bet.owner == player and bet.bet_type == "Pass Line" for bet in table.bets):
                return BetFactory.create_pass_line_bet(self.min_bet, player)
        elif game_state.phase == "point":
            # Reactivate inactive Place bets
            for bet in table.bets:
                if bet.owner == player and bet.bet_type.startswith("Place") and bet.status == "inactive":
                    bet.status = "active"
                    message = f"{player.name}'s {bet.bet_type} bet is now ON."
                    self.play_by_play.write(message)

            # Place Place bets on 5, 6, and 8 during the point phase (excluding the point number)
            numbers = [5, 6, 8]  # Numbers for the Iron Cross

            # Exclude the point number
            if game_state.point in numbers:
                numbers.remove(game_state.point)

            # Filter out numbers already covered by a Place bet
            numbers = [
                num for num in numbers
                if not any(
                    bet.owner == player and bet.bet_type.startswith("Place") and bet.number == num
                    for bet in table.bets
                )
            ]

            # Use the BetFactory to create Place bets
            bets = []
            for number in numbers:
                min_bet = self.table.get_minimum_bet(number)
                bets.append(BetFactory.create_place_bet(min_bet, player, number))

            # Add a Field bet if no active Field bet exists
            if not any(bet.owner == player and bet.bet_type == "Field" for bet in table.bets):
                bets.append(BetFactory.create_field_bet(self.min_bet, player))

            return bets if bets else None

        return None  # No bet to place