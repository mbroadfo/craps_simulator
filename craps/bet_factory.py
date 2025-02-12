# File: .\craps\bet_factory.py

from craps.bets import PassLineBet, PlaceBet, PassLineOddsBet

class BetFactory:
    @staticmethod
    def create_pass_line_bet(amount, owner):
        """Create a Pass Line bet."""
        return PassLineBet(amount, owner)

    @staticmethod
    def create_place_bet(amount, owner, number):
        """Create a Place bet."""
        return PlaceBet(amount, owner, number)

    @staticmethod
    def create_pass_line_odds_bet(amount, owner):
        """Create a Pass Line Odds bet."""
        return PassLineOddsBet(amount, owner)

    @staticmethod
    def create_bets(bet_type, amount, owner, number=None):
        """
        Create one or more bets based on the bet type.
        
        :param bet_type: The type of bet (e.g., "Pass Line", "Place", "Pass Line Odds").
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param number: The number for Place bets (optional).
        :return: A single bet or a list of bets.
        """
        if bet_type == "Pass Line":
            return BetFactory.create_pass_line_bet(amount, owner)
        elif bet_type == "Place":
            return BetFactory.create_place_bet(amount, owner, number)
        elif bet_type == "Pass Line Odds":
            return BetFactory.create_pass_line_odds_bet(amount, owner)
        else:
            raise ValueError(f"Unknown bet type: {bet_type}")