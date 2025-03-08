from typing import List, Optional, Dict, Any, Tuple
from craps.rules import BET_RULES, ODDS_PAYOUT, RESOLUTION_RULES
from craps.bet import Bet
from craps.house_rules import HouseRules

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def find_bet_category(bet_type: str, lookup_table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search for a bet type inside a structured lookup table (BET_RULES, etc.).
        
        :param bet_type: The bet type to search for.
        :param lookup_table: The structured rules dictionary.
        :return: The corresponding bet rules dictionary if found, else None.
        """
        for category, data in lookup_table.items():
            if isinstance(data, dict):  # Ensure we're searching subcategories
                for subcategory, bets in data.items():
                    if isinstance(bets, dict) and bet_type in bets:
                        return bets[bet_type]
                    elif bet_type in data:  # Handles cases where bets are directly under a category
                        return data[bet_type]
        return None

    
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
    def resolve_bet(bet: Bet, dice_outcome: List[int], phase: str, point: Optional[int]) -> int:
        """
        Resolve a bet based on the dice outcome, phase, and point.

        :param bet: The bet object being resolved.
        :param dice_outcome: The dice roll outcome.
        :param phase: The current game phase.
        :param point: The current point (if applicable).
        :return: The payout amount.
        """
        total = sum(dice_outcome)
        sorted_dice = tuple(sorted(dice_outcome))  # Ensures order doesn't matter (e.g., 3-1 == 1-3)
        bet_info = RulesEngine.find_bet_category(bet.bet_type, BET_RULES)

        if not bet_info:
            raise ValueError(f"Unknown bet type: {bet.bet_type}")

        resolution_rules = bet_info["resolution"]

        # Handle `point_made`
        if "point_made" in resolution_rules.get("point_win", []) and total == point:
            bet.status = "won"
        elif "point_made" in resolution_rules.get("point_lose", []) and total == point:
            bet.status = "lost"

        # Handle `number_hit`
        if "number_hit" in resolution_rules.get("point_win", []) and total == bet.number:
            bet.status = "won"
        elif "number_hit" in resolution_rules.get("point_lose", []) and total == bet.number:
            bet.status = "lost"

        # Handle `hardway-win`
        if "hardway-win" in resolution_rules.get("point_win", []) and total in {4, 6, 8, 10} and dice_outcome[0] == dice_outcome[1]:
            bet.status = "won"

        # Handle `hardway-lose`
        if "hardway-lose" in resolution_rules.get("point_lose", []):
            if total == 7 or (total in {4, 6, 8, 10} and dice_outcome[0] != dice_outcome[1]):  # Seven-out or easy way
                bet.status = "lost"

        # Handle `hop` bets (exact dice pair match)
        if "number_hit" in resolution_rules.get("point_win", []) and sorted_dice == (bet.number, bet.number):
            bet.status = "won"
        elif "number_miss" in resolution_rules.get("point_lose", []) and sorted_dice != (bet.number, bet.number):
            bet.status = "lost"

        # Calculate payout if bet was won
        payout = RulesEngine.calculate_payout(bet) if bet.status == "won" else 0
        return payout

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """
        Returns the payout ratio based on bet type and number (if applicable).
        """
        if bet_type in ["Pass Line", "Come"]:
            return (1, 1)
        
        if bet_type in ["Pass Line Odds", "Come Odds"]:
            return ODDS_PAYOUT["True Odds"].get(number, (1, 1))
        
        if bet_type in ["Place", "Place Odds"]:
            return ODDS_PAYOUT["House Odds"].get(number, (1, 1))
        
        if bet_type == "Field":
            return ODDS_PAYOUT["Field Odds"].get(number, (1, 1))
        
        return (1, 1)  # Default payout

    @staticmethod
    def calculate_payout(bet: Bet) -> int:
        """
        Calculate the payout for a resolved bet.
        """
        if bet.status != "won":
            return 0  # No payout if the bet didn't win

        payout_ratio = RulesEngine.get_payout_ratio(bet.bet_type, bet.number)
        numerator, denominator = payout_ratio
        profit = (bet.amount * numerator) // denominator

        if bet.is_contract_bet:
            return bet.amount + profit  # Return original bet + winnings
        return profit  # Return only winnings for non-contract bets

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """
        Get the payout ratio for a bet based on its type and number.
        """
        if bet_type not in BET_PAYOUT:
            raise ValueError(f"Unknown bet type: {bet_type}")

        payout_info = BET_PAYOUT[bet_type]
        
        if payout_info["payout_ratio"] == "True Odds":
            if number is None:
                raise ValueError(f"Number must be provided for True Odds bets.")
            return ODDS_PAYOUT["True Odds"][number]
        
        if payout_info["payout_ratio"] == "House Odds":
            if number is None:
                raise ValueError(f"Number must be provided for House Odds bets.")
            return ODDS_PAYOUT["House Odds"][number]

        if payout_info["payout_ratio"] == "Field Odds":
            return ODDS_PAYOUT["Field Odds"].get(number, (1, 1))  # Default 1:1 payout for non-special numbers

        return payout_info["payout_ratio"]

    
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
