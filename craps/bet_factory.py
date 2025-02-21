# File: .\craps\bet_factory.py

from  .bets.pass_line_bet import PassLineBet  # Import PassLineBet
from .bets.place_bet import PlaceBet  # Import PlaceBet
from .bets.free_odds_bet import FreeOddsBet  # Import FreeOddsBet
from .bets.field_bet import FieldBet  # Import FieldBet
from .bets.come_bet import ComeBet  # Import ComeBet

class BetFactory:
    @staticmethod
    def create_pass_line_bet(amount, owner):
        """Create a Pass Line bet."""
        return PassLineBet(amount, owner)  # Pass the Player object

    @staticmethod
    def create_place_bet(amount, owner, number):
        """Create a Place bet."""
        return PlaceBet(amount, owner, number)  # Pass the Player object

    @staticmethod
    def create_pass_line_odds_bet(amount, owner, number=None):
        """Create a Pass Line Odds bet."""
        return FreeOddsBet("Pass Line Odds", amount, owner, number)  # Pass the Player object and number

    @staticmethod
    def create_place_odds_bet(amount, owner, number):
        """Create a Place Odds bet."""
        return FreeOddsBet("Place Odds", amount, owner, number)  # Pass the Player object and number

    @staticmethod
    def create_field_bet(amount, owner):
        """Create a Field bet."""
        return FieldBet(amount, owner)  # Pass the Player object

    @staticmethod
    def create_come_bet(amount, owner):
        """Create a Come bet."""
        return ComeBet(amount, owner)  # Pass the Player object

    @staticmethod
    def create_bets(bet_type, amount, owner, number=None):
        """
        Create one or more bets based on the bet type.
        
        :param bet_type: The type of bet (e.g., "Pass Line", "Place", "Place Odds", "Field", "Come").
        :param amount: The amount of the bet.
        :param owner: The Player object who placed the bet.
        :param number: The number for Place or Place Odds bets (optional).
        :return: A single bet or a list of bets.
        """
        if bet_type == "Pass Line":
            return BetFactory.create_pass_line_bet(amount, owner)
        elif bet_type == "Place":
            return BetFactory.create_place_bet(amount, owner, number)
        elif bet_type == "Place Odds":
            return BetFactory.create_place_odds_bet(amount, owner, number)
        elif bet_type == "Field":
            return BetFactory.create_field_bet(amount, owner)
        elif bet_type == "Come":
            return BetFactory.create_come_bet(amount, owner)
        else:
            raise ValueError(f"Unknown bet type: {bet_type}")