# File: .\craps\rules_engine.py

from typing import List, Optional, Dict, Any, Tuple
from craps.rules import BET_RULES, BET_PAYOUT, ODDS_PAYOUT
from craps.bet import Bet 
from craps.house_rules import HouseRules

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    def __init__(self, house_rules):
        """
        Initialize the RulesEngine with house rules.
        """
        self.house_rules = house_rules
        
    @staticmethod
    def get_minimum_bet(number: Optional[int] = None, house_rules: Optional[HouseRules] = None) -> int:
        """
        Get the minimum bet amount for a specific bet type or number.
        - For Place bets on 6 and 8, the minimum is table minimum + table unit.
        - For all other bets, it's the table minimum.
        """
        if house_rules is None:
            raise ValueError("HouseRules must be provided to determine minimum bet.")

        table_minimum = house_rules.table_minimum
        table_unit = table_minimum // 5  # Typically, the unit is 1/5 of the table minimum

        if number in [6, 8]:
            return table_minimum + table_unit  # 6 and 8 require an extra unit
        return table_minimum  # Default to table minimum for all other bets

    @staticmethod
    def can_make_bet(bet_type: str, phase: str, parent_bet: Optional[Bet] = None) -> bool:
        """
        Determine if a bet of the given type can be made during the current phase.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # Check if the bet is allowed in the current phase
        if phase not in BET_RULES[bet_type]["valid_phases"]:
            return False

        # Additional checks for odds bets
        if bet_type.endswith("Odds"):
            if parent_bet is None:
                return False  # Parent bet is required for odds bets
            if bet_type == "Come Odds" and parent_bet.number is None:
                return False  # Come bet must have a number set

        return True
    
    @staticmethod
    def create_bet(bet_type: str, amount: int, owner, number: Optional[int] = None, parent_bet: Optional[Bet] = None) -> Bet:
        """
        Create a bet based on the bet type.
        """
        if bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # Validate the bet can be created
        if not RulesEngine.can_make_bet(bet_type, "come-out" if number is None else "point", parent_bet):
            raise ValueError(f"Cannot create {bet_type} bet in the current phase or conditions.")

        payout_ratio = RulesEngine.get_payout_ratio(bet_type, number)
        vig = RulesEngine.has_vig(bet_type)
        is_contract_bet = BET_RULES[bet_type]["is_contract_bet"]
        valid_phases = BET_RULES[bet_type]["valid_phases"]

        return Bet(
            bet_type=bet_type,
            amount=amount,
            owner=owner,
            payout_ratio=payout_ratio,
            vig=vig,
            valid_phases=valid_phases,
            number=number,
            parent_bet=parent_bet,
            is_contract_bet=is_contract_bet,
        )

    @staticmethod
    def can_remove_bet(bet: Bet) -> bool:
        """
        Determine if a bet can be removed.
        Contract bets cannot be removed. Non-contract bets can be removed.
        """
        return not bet.is_contract_bet

    @staticmethod
    def can_turn_on(bet: Bet, puck_position: str) -> bool:
        """
        Determine if a bet can be turned on.
        - Contract bets are always on and cannot be turned on/off.
        - Non-contract bets can only be turned on when the puck is off.
        """
        if bet.is_contract_bet:
            return False  # Contract bets are always on and cannot be turned on/off
        return puck_position == "Off"  # Non-contract bets can only be turned on when the puck is off

    @staticmethod
    def resolve_bet(bet: Bet, dice_outcome: List[int], phase: str, point: Optional[int], puck_position: str) -> int:
        """
        Resolve a bet and return the payout amount.
        - For contract bets: the bet is cleared if it is won or lost.
        - For non-contract bets: the bet is cleared only if it is lost.
        """
        if bet.bet_type not in BET_RULES:
            raise ValueError(f"Unknown bet type: {bet.bet_type}")

        total = sum(dice_outcome)
        behavior = BET_RULES[bet.bet_type]["after_roll"][phase]

        # Handle Come bet movement to a number
        if bet.bet_type == "Come" and phase == "point" and total in [4, 5, 6, 8, 9, 10]:
            bet.number = total
            bet.valid_phases = ["point"]  # Come bets are always on after moving to a number
            return 0  # No payout for moving to a number

        # Handle winning conditions
        if behavior["winning"] is not None:
            if isinstance(behavior["winning"], list) and "Number" in behavior["winning"]:
                if total == bet.number:
                    bet.status = "won"
            elif total in behavior["winning"] or (isinstance(behavior["winning"], list) and "Point" in behavior["winning"] and total == point):
                bet.status = "won"

        # Handle losing conditions
        if behavior["losing"] is not None:
            if total in behavior["losing"]:
                bet.status = "lost"

        # Calculate the payout
        payout = RulesEngine.calculate_payout(bet)

        # Update bet status for non-contract bets
        if not bet.is_contract_bet and bet.status == "won":
            if puck_position == "Off":
                bet.status = "inactive"  # Puck is off, so the bet is inactive
            else:
                bet.status = "active"  # Puck is on, so the bet remains active

        return payout

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
    def calculate_payout(bet: Bet) -> int:
        """
        Calculate the payout for a resolved bet.
        - For contract bets: return the original bet amount + winnings.
        - For non-contract bets: return only the winnings.
        """
        if bet.status != "won":
            return 0  # No payout if the bet didn't win

        numerator, denominator = bet.payout_ratio
        profit = (bet.amount * numerator) // denominator

        if bet.is_contract_bet:
            return bet.amount + profit  # Return original bet + winnings
        return profit  # Return only winnings for non-contract bets
    
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