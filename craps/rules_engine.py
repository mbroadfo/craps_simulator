# File: .\craps\rules_engine.py

from typing import List, Optional, Dict, Any, Tuple
from craps.rules import BET_BEHAVIOR, BET_PAYOUT, ODDS_PAYOUT
from craps.bet import Bet  # Import the Bet class

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
        if bet_type not in BET_BEHAVIOR:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # Get the payout ratio and other properties from the RulesEngine
        payout_ratio = RulesEngine.get_payout_ratio(bet_type, number)
        vig = RulesEngine.has_vig(bet_type)

        # Get the is_contract_bet and valid_phases from the top level
        is_contract_bet = BET_BEHAVIOR[bet_type]["is_contract_bet"]
        valid_phases = BET_BEHAVIOR[bet_type]["valid_phases"]

        # Create the bet
        bet = Bet(
            bet_type=bet_type,
            amount=amount,
            owner=owner,
            payout_ratio=payout_ratio,
            vig=vig,
            valid_phases=valid_phases,
            number=number,
            parent_bet=parent_bet,
            is_contract_bet=is_contract_bet,  # Pass the is_contract_bet value
        )

        return bet

    @staticmethod
    def can_make_bet(bet_type: str, phase: str, parent_bet: Optional[Bet] = None) -> bool:
        """
        Determine if a bet of the given type can be made during the current phase.

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :param phase: The current game phase ("come-out" or "point").
        :param parent_bet: The parent bet for odds bets.
        :return: True if the bet can be made, False otherwise.
        """
        if bet_type not in BET_BEHAVIOR:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # Check if the bet is allowed in the current phase
        if phase not in BET_BEHAVIOR[bet_type]["valid_phases"]:
            return False

        # Additional checks for odds bets
        if bet_type.endswith("Odds"):
            if parent_bet is None:
                return False  # Parent bet is required for odds bets
            if bet_type == "Come Odds" and parent_bet.number is None:
                return False  # Come bet must have a number set

        return BET_BEHAVIOR[bet_type][phase]["can_bet"]

    @staticmethod
    def can_remove_bet(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be removed during the current phase.

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
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

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
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

        # Handle Field bet payouts dynamically
        if bet.bet_type == "Field":
            if total in ODDS_PAYOUT["Field Odds"]:
                bet.payout_ratio = ODDS_PAYOUT["Field Odds"][total]  # Set payout ratio for 2 or 12
            else:
                bet.payout_ratio = (1, 1)  # Default payout ratio for other winning numbers

        # Check if the bet wins
        if behavior["winning"] is not None:
            if isinstance(behavior["winning"], list) and "Number" in behavior["winning"]:
                # For Place bets, check if the total matches the bet's number
                if total == bet.number:
                    bet.status = "won"
                    return None
            elif total in behavior["winning"] or (isinstance(behavior["winning"], list) and "Point" in behavior["winning"] and total == point):
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
                bet.status = "active"  # Ensure the bet remains active
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

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
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
        elif payout_info["payout_ratio"] == "Field Odds":
            if number is None:
                return (1, 1)  # Default payout for Field bet
            return ODDS_PAYOUT["Field Odds"].get(number, (1, 1))  # Use special payouts for 2 and 12
        else:
            return payout_info["payout_ratio"]

    @staticmethod
    def has_vig(bet_type: str) -> bool:
        """
        Determine if a bet of the given type has a vig (commission).

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :return: True if the bet has a vig, False otherwise.
        """
        if bet_type not in BET_PAYOUT:
            raise ValueError(f"Unknown bet type: {bet_type}")

        return BET_PAYOUT[bet_type]["vig"]

    @staticmethod
    def get_linked_bet_type(bet_type: str) -> Optional[str]:
        """
        Get the type of bet linked to the given bet type (e.g., Pass Line Odds is linked to Pass Line).

        :param bet_type: The type of bet (e.g., "Pass Line", "Pass Line Odds", "Place").
        :return: The linked bet type, or None if no linked bet exists.
        """
        linked_bets = {
            "Pass Line": "Pass Line Odds",
            "Come": "Come Odds",
            "Place": "Place Odds",
        }
        return linked_bets.get(bet_type)