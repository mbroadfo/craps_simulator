# File: .\craps\bet_factory.py

from typing import Optional
from craps.bet import Bet
from craps.rules_engine import RulesEngine

class BetFactory:
    @staticmethod
    def create_bet(bet_type: str, amount: int, owner, number: Optional[int] = None, parent_bet: Optional[Bet] = None) -> Bet:
        """
        Create a bet based on the bet type.

        :param bet_type: The type of bet (e.g., "Pass Line", "Place").
        :param amount: The amount of the bet.
        :param owner: The player who placed the bet.
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :param parent_bet: The parent bet for odds bets.
        :return: A Bet instance.
        """
        # Get the payout ratio and other properties from the RulesEngine
        payout_ratio = RulesEngine.get_payout_ratio(bet_type, number)
        vig = RulesEngine.has_vig(bet_type)
        valid_phases = ["come-out", "point"]  # Default valid phases

        # Create the bet
        bet = Bet(
            bet_type=bet_type,
            amount=amount,
            owner=owner,
            payout_ratio=payout_ratio,
            vig=vig,
            valid_phases=valid_phases,
            number=number,
            parent_bet=parent_bet
        )

        return bet