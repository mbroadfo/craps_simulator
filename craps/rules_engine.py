from typing import List, Optional, Dict, Any, Tuple
from craps.rules import BET_RULES, BET_PAYOUT
from craps.bet import Bet
from craps.house_rules import HouseRules

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def find_bet_category(bet_type, lookup_table=BET_RULES):
        """Find the category a bet type belongs to."""
        for category, rules in lookup_table.items():
            if bet_type in rules:
                return category
        raise ValueError(f"Unknown bet type: {bet_type}")
    
    @staticmethod
    def get_linked_bet_type(bet_type):
        """Retrieve the linked bet type, if applicable (e.g., Pass Line → Pass Line Odds)."""
        bet_category = RulesEngine.find_bet_category(bet_type)  # ✅ Get category name
        bet_info = BET_RULES[bet_category][bet_type]  # ✅ Now correctly accessing bet rules
        return bet_info.get("linked_bet")  # ✅ Safely retrieve linked bet

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
        bet_category = RulesEngine.find_bet_category(bet_type)
        bet_rules = BET_RULES[bet_category][bet_type]

        if not bet_rules:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # Skip payout lookup for bets that require the roll (like Field)
        payout_ratio = None if bet_type == "Field" else RulesEngine.get_payout_ratio(bet_type, number)

        return Bet(
            bet_type=bet_type,
            amount=amount,
            owner=owner,
            payout_ratio=payout_ratio,  # Field will calculate this later
            valid_phases=bet_rules["valid_phases"],
            number=number,
            parent_bet=parent_bet,
            is_contract_bet=bet_rules.get("is_contract_bet", False),
        )

    @staticmethod
    def can_make_bet(bet_type, phase):
        """Check if a bet type is allowed in the current phase."""
        bet_category = RulesEngine.find_bet_category(bet_type)  # ✅ Get category name
        bet_info = BET_RULES[bet_category][bet_type]  # ✅ Now correctly accessing bet rules

        return phase in bet_info["valid_phases"]

    @staticmethod
    def can_remove_bet(bet_type: str, phase: str) -> bool:
        """
        Determine if a bet of the given type can be removed during the current phase.
        Contract bets cannot be removed once placed.
        """
        # Find the bet type inside BET_RULES
        for category, data in BET_RULES.items():
            if isinstance(data, dict):
                if bet_type in data:  # Direct match in category
                    bet_info = data[bet_type]
                    category_info = data
                    break
                for subcategory, bets in data.items():
                    if isinstance(bets, dict) and bet_type in bets:  # Found inside a subcategory
                        bet_info = bets[bet_type]
                        category_info = data
                        break
        else:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # Check if it's a contract bet at the bet or category level
        if bet_info.get("is_contract_bet", False) or category_info.get("is_contract_bet", False):
            return False  # Contract bets cannot be removed

        return True

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
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """
        Get the payout ratio for a bet based on its type and number (if applicable).

        :param bet_type: The type of bet (e.g., "Pass Line", "Place", "Any Seven").
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :return: A tuple representing the payout ratio (e.g., (2, 1) for 2:1).
        """
        bet_category = RulesEngine.find_bet_category(bet_type)  # ✅ Get category name
        bet_info = BET_RULES[bet_category][bet_type]  # ✅ Now correctly accessing bet rules
        payout_key = bet_info["payout_ratio"]  # ✅ Safe lookup

        # Now apply the logic for payout lookup
        if payout_key in BET_PAYOUT:
            if "default" in BET_PAYOUT[payout_key]:
                return BET_PAYOUT[payout_key]["default"]
            if number is not None and number in BET_PAYOUT[payout_key]:
                return BET_PAYOUT[payout_key][number]

        raise ValueError(f"Invalid payout type {payout_key} for bet {bet_type} (number={number})")

    @staticmethod
    def resolve_bet(bet: Bet, dice_outcome: List[int], phase: str, point: Optional[int]) -> int:
        """
        Resolves a bet based on the dice outcome, phase, and point.
        Uses a structured approach based on bet categories.
        """
        total = sum(dice_outcome)
        is_pair = dice_outcome[0] == dice_outcome[1]
        sorted_dice = tuple(sorted(dice_outcome))
        bet_info = RulesEngine.find_bet_category(bet.bet_type, BET_RULES)

        if not bet_info:
            raise ValueError(f"Unknown bet type: {bet.bet_type}")

        result = RulesEngine.find_bet_category(bet.bet_type, BET_RULES)
        if isinstance(result, tuple) and len(result) == 2:
            bet_category, bet_rules = result
        else:
            raise ValueError(f"Unexpected return value from find_bet_category: {result}")

        resolution_rules = BET_RULES[bet_category][bet.bet_type]["resolution"]

        # 🎯 **1. LINE BETS (Pass Line, Don't Pass, Come, Don't Come)**
        if bet.bet_type in BET_RULES["Line Bets"]:
            bet_category, bet_rules = RulesEngine.find_bet_category(bet.bet_type, BET_RULES)  # ✅ Get correct rules
            resolution_rules = bet_rules["resolution"]  # ✅ Extract win/loss conditions

            # 🔎 **Extract Win/Loss Conditions**
            winning_numbers = resolution_rules.get(f"{phase}_win", [])
            losing_numbers = resolution_rules.get(f"{phase}_lose", [])

            print(f"DEBUG: Resolving {bet.bet_type} | Phase: {phase} | Total: {total} | Point: {point}")
            print(f"DEBUG: Expected Winning Numbers: {winning_numbers}")
            print(f"DEBUG: Expected Losing Numbers: {losing_numbers}")

            # 🏆 **Check if the bet wins**
            if total in winning_numbers:
                bet.status = "won"
                print(f"DEBUG: {bet.bet_type} WON on {total}")

            # ❌ **Check if the bet loses**
            elif total in losing_numbers:
                bet.status = "lost"
                print(f"DEBUG: {bet.bet_type} LOST on {total}")

            # 🎯 **Handle "point_made" for Pass Line & "number_hit" for Come**
            elif "point_made" in winning_numbers and total == point:
                bet.status = "won"
                print(f"DEBUG: {bet.bet_type} WON - Point {point} Made!")

            elif "number_hit" in winning_numbers and total == bet.number:
                bet.status = "won"
                print(f"DEBUG: {bet.bet_type} WON - Number {bet.number} Hit!")

            # ❌ **Handle "point_made" for Don't Pass & "number_hit" for Don't Come**
            elif "point_made" in losing_numbers and total == point:
                bet.status = "lost"
                print(f"DEBUG: {bet.bet_type} LOST - Point {point} Made!")

            elif "number_hit" in losing_numbers and total == bet.number:
                bet.status = "lost"
                print(f"DEBUG: {bet.bet_type} LOST - Number {bet.number} Hit!")
                
        ### 🎯 **2. FIELD BETS**
        elif bet.bet_type == "Field":
            if "in-field" in resolution_rules.get(f"{phase}_win", []):
                bet.status = "won"
                bet.number = total  # ✅ Set the number to the rolled value
            elif "out-field" in resolution_rules.get(f"{phase}_lose", []):
                bet.status = "lost"

        ### 🎯 **3. PLACE, BUY, LAY BETS**
        elif bet.bet_type in BET_RULES["Place Bets"]:
            if total == bet.number and "number_hit" in resolution_rules.get(f"{phase}_win", []):
                bet.status = "won"
            elif total == 7 and "point_lose" in resolution_rules.get(f"{phase}_lose", []):
                bet.status = "lost"

        ### 🎯 **4. PROPOSITION BETS**
        elif bet.bet_type == "Proposition":
            if "number_hit" in resolution_rules.get(f"{phase}_win", []):
                bet.status = "won"
            elif "any_other" in resolution_rules.get(f"{phase}_lose", []):
                bet.status = "lost"

        ### 🎯 **5. HARDWAYS**
        elif bet.bet_type == "Hardways":
            if "hardway_win" in resolution_rules.get(f"{phase}_win", []):
                if total == bet.number and is_pair:
                    bet.status = "won"

            if "hardway_lose" in resolution_rules.get(f"{phase}_lose", []):
                if total == 7 or (total == bet.number and not is_pair):  # ✅ Easy way loses
                    bet.status = "lost"

        ### 🎯 **6. HOP BETS**
        elif bet.bet_type == "Hop":
            if "hop_win" in resolution_rules.get(f"{phase}_win", []):
                if sorted_dice == (bet.number, bet.number) or sorted_dice in BET_PAYOUT["Hop"]:
                    bet.status = "won"
            elif "hop_lose" in resolution_rules.get(f"{phase}_lose", []):
                if sorted_dice != (bet.number, bet.number) and sorted_dice not in BET_PAYOUT["Hop"]:
                    bet.status = "lost"

        ### 🎯 **Calculate Payout if Won**
        payout = RulesEngine.calculate_payout(bet, total) if bet.status == "won" else 0
        return payout

    @staticmethod
    def calculate_payout(bet: Bet, roll: Optional[int] = None) -> int:
        """
        Calculate the payout for a resolved bet.
        """
        if bet.status != "won":
            return 0  # No payout if the bet didn't win

        payout_ratio = RulesEngine.get_payout_ratio(bet.bet_type, bet.number)

        # Ensure the correct roll value is used for bets that depend on it (e.g., Field)
        number = roll if bet.bet_type == "Field" else bet.number

        payout_ratio = RulesEngine.get_payout_ratio(bet.bet_type, number)
        numerator, denominator = payout_ratio
        profit = (bet.amount * numerator) // denominator

        return bet.amount + profit if bet.is_contract_bet else profit

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
    