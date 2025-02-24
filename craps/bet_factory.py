# File: .\craps\bet_factory.py

from  .bets.pass_line_bet import PassLineBet 
from .bets.place_bet import PlaceBet 
from .bets.free_odds_bet import FreeOddsBet
from .bets.field_bet import FieldBet
from .bets.come_bet import ComeBet

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
    def create_come_bet(amount, owner, come_odds_working_on_come_out=False):
        """Create a Come bet."""
        return ComeBet(amount, owner, come_odds_working_on_come_out)

    @staticmethod
    def create_pass_line_odds_bet(amount, owner, parent_bet):
        """Create a Pass Line Odds bet linked to a Pass Line bet."""
        if parent_bet.bet_type != "Pass Line":
            raise ValueError("Pass Line Odds must be linked to a Pass Line bet")
        return FreeOddsBet("Pass Line Odds", amount, owner, parent_bet)

    @staticmethod
    def create_place_odds_bet(amount, owner, parent_bet):
        """Create a Place Odds bet linked to a Place bet."""
        if parent_bet.bet_type != "Place":
            raise ValueError("Place Odds must be linked to a Place bet")
        return FreeOddsBet("Place Odds", amount, owner, parent_bet)

    @staticmethod
    def create_come_odds_bet(amount, owner, parent_bet):
        """Create a Come Odds bet linked to a Come bet."""
        if parent_bet.bet_type != "Come":
            raise ValueError("Come Odds must be linked to a Come bet")
        if parent_bet.number is None:
            raise ValueError("Come bet must have a number before placing odds")
        return FreeOddsBet("Come Odds", amount, owner, parent_bet)
    
    @staticmethod
    def create_field_bet(amount, owner):
        """Create a Field bet."""
        return FieldBet(amount, owner)

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
        elif bet_type == "Pass Line Odds":
            return BetFactory.create_pass_line_bet(amount, owner)
        elif bet_type == "Place":
            return BetFactory.create_place_bet(amount, owner, number)
        elif bet_type == "Place Odds":
            return BetFactory.create_place_odds_bet(amount, owner, number)
        elif bet_type == "Come":
            return BetFactory.create_come_bet(amount, owner)
        elif bet_type == "Come Odds":
            return BetFactory.create_come_bet(amount, owner)
        elif bet_type == "Field":
            return BetFactory.create_field_bet(amount, owner)
        else:
            raise ValueError(f"Unknown bet type: {bet_type}")