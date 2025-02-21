# File: .\craps\strategies\three_point_molly_strategy.py

from craps.bet_factory import BetFactory

class ThreePointMollyStrategy:
    """Betting strategy for the 3-Point Molly system."""
    def __init__(self, min_bet, odds_multiple=1):
        """
        Initialize the 3-Point Molly strategy.

        :param min_bet: The minimum bet amount for the table.
        :param odds_multiple: The multiple of the minimum bet to use for odds (e.g., 1x, 2x).
        """
        self.min_bet = min_bet
        self.odds_multiple = odds_multiple

    def get_bet(self, game_state, player, table):
        """
        Place bets according to the 3-Point Molly strategy.

        :param game_state: The current game state.
        :param player: The player placing the bets.
        :param table: The table to place the bets on.
        :return: A list of bets to place.
        """
        bets = []

        # Place a Pass Line bet if no active Pass Line bet exists (only during come-out phase)
        if game_state.phase == "come-out":
            if not any(bet.bet_type == "Pass Line" for bet in table.bets if bet.owner == player):
                bets.append(BetFactory.create_pass_line_bet(self.min_bet, player))

        # Place up to 3 Come bets if fewer than 3 active Come bets exist (only during point phase)
        if game_state.phase == "point":
            active_come_bets = [bet for bet in table.bets if bet.bet_type == "Come" and bet.owner == player]
            if len(active_come_bets) < 3:
                bets.append(BetFactory.create_come_bet(self.min_bet, player))

        # Place odds on active Pass Line and Come bets (only during point phase)
        if game_state.phase == "point":
            for bet in table.bets:
                if bet.owner == player:
                    if bet.bet_type == "Pass Line" and bet.status == "active":
                        # Place Pass Line Odds
                        odds_amount = self.min_bet * self.odds_multiple
                        bets.append(BetFactory.create_pass_line_odds_bet(odds_amount, player, game_state.point))
                    elif bet.bet_type == "Come" and bet.status == "active" and bet.number is not None:
                        # Place Come Odds
                        odds_amount = self.min_bet * self.odds_multiple
                        bets.append(BetFactory.create_come_odds_bet(odds_amount, player, bet.number))

        return bets if bets else None