from typing import List, Optional, Tuple
from craps.rules import BET_RULES, get_payout_ratio
from craps.bet import Bet

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def get_minimum_bet(number: Optional[int] = None) -> int:
        """
        Get the minimum bet amount for a specific bet type or number.

        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :return: The minimum bet amount.
        """
        # Default minimum bet for most bets
        default_min_bet = 10  # Replace with the actual default minimum bet from house rules

        # Adjust minimum bet for specific bet types or numbers
        if number is not None:
            # For Place bets, the minimum bet may vary based on the number
            if number in [4, 5, 6, 8, 9, 10]:
                return default_min_bet  # Replace with actual logic if needed
            else:
                raise ValueError(f"Invalid number for minimum bet: {number}")

        return default_min_bet

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
        bet_rules = None
        for category in BET_RULES.values():
            if bet_type in category:
                bet_rules = category[bet_type]
                break

        if not bet_rules:
            raise ValueError(f"Unknown bet type: {bet_type}")

        payout_ratio = get_payout_ratio(bet_type, number)

        return Bet(
            bet_type=bet_type,
            amount=amount,
            owner=owner,
            payout_ratio=payout_ratio,
            valid_phases=bet_rules["valid_phases"],
            number=number,
            parent_bet=parent_bet,
            is_contract_bet=bet_rules.get("is_contract_bet", False),
        )

    @staticmethod
    def can_make_bet(bet_type: str, phase: str, parent_bet: Optional[Bet] = None) -> bool:
        """
        Determine if a bet of the given type can be made during the current phase.

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :param parent_bet: The parent bet for odds bets.
        :return: True if the bet can be made, False otherwise.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")
        return phase in BET_RULES[bet_type]["valid_phases"]

    @staticmethod
    def can_remove_bet(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be removed during the current phase.

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet can be removed, False otherwise.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")
        return BET_RULES[bet_type].get("can_remove", False)

    @staticmethod
    def can_turn_on(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be turned on during the current phase.

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet can be turned on, False otherwise.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")
        return BET_RULES[bet_type].get("can_turn_on", False)

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
        total = sum(dice_outcome)
        bet_rules = None

        for category in BET_RULES.values():
            if bet.bet_type in category:
                bet_rules = category[bet.bet_type]
                break

        if not bet_rules:
            raise ValueError(f"Unknown bet type: {bet.bet_type}")

        if total in bet_rules.get("winning", []):
            bet.status = "won"
        elif total in bet_rules.get("losing", []):
            bet.status = "lost"
        elif bet_rules.get("other_action") == "Moves to Number":
            bet.number = total
            bet.valid_phases = ["point"]
        elif bet_rules.get("other_action") == "Sets the Point":
            return total

        return None

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """
        Get the payout ratio for a bet based on its type and number.

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :return: A tuple representing the payout ratio (numerator, denominator).
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")
        return get_payout_ratio(bet_type, number)
    
    @staticmethod
    def has_vig(bet_type: str) -> bool:
        """
        Determine if a bet of the given type has a vig (commission).

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :return: True if the bet has a vig, False otherwise.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")
        return BET_RULES[bet_type].get("vig", False)
    
    @staticmethod
    def get_linked_bet_type(bet_type: str) -> Optional[str]:
        """
        Get the type of bet linked to the given bet type (e.g., Pass Line Odds is linked to Pass Line).

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :return: The linked bet type, or None if no linked bet exists.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")
        return BET_RULES[bet_type].get("linked_bet")
