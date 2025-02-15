from craps.bet_factory import BetFactory
from craps.bets.pass_line import PassLineBet

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
                return BetFactory.create_pass_line_bet(self.min_bet, player.name)
        elif game_state.phase == "point":
            # Place Place bets on 5, 6, and 8 during the point phase
            numbers = [5, 6, 8]  # Numbers for the Iron Cross

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
                bets.append(BetFactory.create_place_bet(min_bet, player.name, number))

            return bets if bets else None

        return None  # No bet to place