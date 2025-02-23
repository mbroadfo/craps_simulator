# File: .\craps\rules_engine.py

from typing import List, Optional, Dict, Any, Tuple
from craps.bet import Bet
from craps.rules import BET_BEHAVIOR, BET_PAYOUT, ODDS_PAYOUT

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def can_make_bet(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be made during the current phase.

        :param bet_type: The type of bet (e.g., "Pass", "Pass Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet can be made, False otherwise.
        """
        if bet_type not in BET_BEHAVIOR:
            raise ValueError(f"Unknown bet type: {bet_type}")
        
        return BET_BEHAVIOR[bet_type][phase]["can_bet"]

    @staticmethod
    def can_remove_bet(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be removed during the current phase.

        :param bet_type: The type of bet (e.g., "Pass", "Pass Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet can be removed, False otherwise.
        """
        if bet_type not in BET_BEHAVIOR:
            raise ValueError(f"Unknown bet type: {bet_type}")
        
        return BET_BEHAVIOR[bet_type][phase]["can_remove"]

    @staticmethod
    def can_turn_on(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be turned on during the current phase.

        :param bet_type: The type of bet (e.g., "Pass", "Pass Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet can be turned on, False otherwise.
        """
        if bet_type not in BET_BEHAVIOR:
            raise ValueError(f"Unknown bet type: {bet_type}")
        
        return BET_BEHAVIOR[bet_type][phase]["can_turn_on"]

    @staticmethod
    def resolve_bet(bet: Bet, dice_outcome: List[int], phase: str, point: Optional[int]) -> Optional[int]:
        """
        Resolve a bet based on the dice outcome, phase, and point.

        :param bet: The bet to resolve.
        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        :return: The new point number if the bet sets the point, otherwise None.
        """
        if bet.bet_type not in BET_BEHAVIOR:
            raise ValueError(f"Unknown bet type: {bet.bet_type}")

        total = sum(dice_outcome)
        behavior = BET_BEHAVIOR[bet.bet_type][phase]

        # Check if the bet wins
        if behavior["winning"] is not None:
            if total in behavior["winning"] or (isinstance(behavior["winning"], list) and "Point" in behavior["winning"] and total == point):
                bet.status = "won"
                return None

        # Check if the bet loses
        if behavior["losing"] is not None:
            if total in behavior["losing"]:
                bet.status = "lost"
                return None

        # Handle other actions (e.g., setting the point or moving a Come bet)
        if behavior["other_action"] is not None:
            if behavior["other_action"] == "Sets the Point":
                # Set the point for Pass Line bets
                return total
            elif behavior["other_action"] == "Moves to Number":
                # Move Come bets to the number rolled
                bet.number = total
                bet.valid_phases = ["point"]  # Now only valid during the point phase

        # If neither, the bet remains active
        bet.status = "active"
        return None

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """
        Get the payout ratio for a bet based on its type and number.

        :param bet_type: The type of bet (e.g., "Pass", "Pass Odds", "Place").
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :return: A tuple representing the payout ratio (numerator, denominator).
        """
        if bet_type not in BET_PAYOUT:
            raise ValueError(f"Unknown bet type: {bet_type}")

        payout_info = BET_PAYOUT[bet_type]
        if payout_info["payout_ratio"] == "True Odds":
            if number is None:
                raise ValueError(f"Number must be provided for True Odds bets.")
            return ODDS_PAYOUT["True Odds"][number]
        elif payout_info["payout_ratio"] == "House Odds":
            if number is None:
                raise ValueError(f"Number must be provided for House Odds bets.")
            return ODDS_PAYOUT["House Odds"][number]
        else:
            return payout_info["payout_ratio"]

    @staticmethod
    def has_vig(bet_type: str) -> bool:
        """
        Determine if a bet of the given type has a vig (commission).

        :param bet_type: The type of bet (e.g., "Pass", "Pass Odds", "Place").
        :return: True if the bet has a vig, False otherwise.
        """
        if bet_type not in BET_PAYOUT:
            raise ValueError(f"Unknown bet type: {bet_type}")

        return BET_PAYOUT[bet_type]["vig"]

    @staticmethod
    def get_linked_bet_type(bet_type: str) -> Optional[str]:
        """
        Get the type of bet linked to the given bet type (e.g., Pass Line Odds is linked to Pass Line).

        :param bet_type: The type of bet (e.g., "Pass", "Pass Odds", "Place").
        :return: The linked bet type, or None if no linked bet exists.
        """
        linked_bets = {
            "Pass": "Pass Odds",
            "Come": "Come Odds",
            "Place": "Place Odds",
        }
        return linked_bets.get(bet_type)