# File: craps/strategies/iron_cross.py
from craps.bet_factory import BetFactory

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

    def get_bet(self, game_state, player):
        """Place bets for the Iron Cross strategy."""
        if game_state.phase == "come-out":
            # Place a Pass Line bet during the come-out roll if no active bet exists
            if not any(b.bet_type == "Pass Line" for b in player.active_bets):
                return BetFactory.create_pass_line_bet(self.min_bet, player)  # Pass the Player object
        elif game_state.phase == "point":
            # Reactivate inactive Place bets
            for bet in player.active_bets:
                if bet.bet_type.startswith("Place") and bet.status == "inactive":
                    bet.status = "active"
                    print(f"{player.name}'s {bet.bet_type} bet is now ON.")

            # Place Place bets on 5, 6, and 8 during the point phase (excluding the point number)
            numbers = [5, 6, 8]  # Numbers for the Iron Cross

            # Exclude the point number
            if game_state.point in numbers:
                numbers.remove(game_state.point)

            # Filter out numbers already covered by a Place bet
            numbers = [
                num for num in numbers
                if not any(
                    b.bet_type.startswith("Place") and b.number == num
                    for b in player.active_bets
                )
            ]

            # Use the BetFactory to create Place bets
            bets = []
            for number in numbers:
                min_bet = self.table.get_minimum_bet(number)
                bets.append(BetFactory.create_place_bet(min_bet, player, number))

            # Add a Field bet if no active Field bet exists
            if not any(b.bet_type == "Field" for b in player.active_bets):
                bets.append(BetFactory.create_field_bet(self.min_bet, player))

            return bets if bets else None

        return None  # No bet to place