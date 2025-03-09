from typing import List, Optional, Dict, Any, Tuple
from craps.rules import BET_RULES, BET_PAYOUT
from craps.bet import Bet
from craps.house_rules import HouseRules

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def find_bet_category(bet_type: str) -> tuple:
        """Find the category and rules for a given bet type."""
        for category, bets in BET_RULES.items():
            if bet_type in bets:
                return category, bets[bet_type]  # ✅ Return both category & rules

        raise ValueError(f"Unknown bet type: {bet_type}")
    
    @staticmethod
    def get_linked_bet_type(bet_type: str) -> Optional[str]:
        """Returns the linked bet type, if any (e.g., Pass Line → Pass Line Odds)."""
        _, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Get correct bet rules

        return bet_info.get("linked_bet") if isinstance(bet_info, dict) else None  # ✅ Fix

    @staticmethod
    def get_minimum_bet(bet_type: str, table_min: int, table_max: int) -> int:
        """Returns the correct minimum bet amount for a given bet type based on table rules."""
        bet_category, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Get correct bet rules

        # 🟢 **Base Minimum Bet: All bets must be at least $1**
        min_bet = 1

        # 🟢 **Line & Field Bets: Must be within table min & max**
        if bet_category in ["Line Bets", "Field Bets"]:
            min_bet = max(table_min, min_bet)  # Ensure at least table minimum
            return min(table_max, min_bet)  # Ensure it doesn't exceed table max

        # 🟢 **Prop, Hop, Hardways, Odds Bets: Can be as low as $1**
        elif bet_category in ["Other Bets", "Odds Bets"]:
            return min_bet  # No additional constraints

        # 🟢 **Place & Don't Place Bets: Special Case for 6 & 8**
        elif bet_category == "Place Bets":
            if bet_type in ["Place", "Don't Place"] and bet_info.get("number") in [6, 8]:
                return table_min + (table_min // 5)  # Ensure correct payout increments
            return table_min  # Regular place bets follow the table minimum

        # 🟢 **Odds on 5 & 9: Must be Even for Correct Payouts**
        elif bet_category == "Odds Bets" and bet_info.get("number") in [5, 9]:
            return max(2, (table_min // 2) * 2)  # Round up to the nearest even number

        return min_bet  # Default minimum bet

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
    def can_make_bet(bet_type: str, phase: str) -> bool:
        """Check if a bet type is allowed in the current phase."""
        _, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Fetch correct bet rules
        return phase in bet_info["valid_phases"]  # ✅ Safe lookup

    @staticmethod
    def can_remove_bet(bet_type: str, phase: str) -> bool:
        """Determine if a bet can be removed during the current phase."""
        _, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Use standard lookup

        # ✅ Only check `is_contract_bet` at the bet level
        return not bet_info.get("is_contract_bet", False)

    @staticmethod
    def can_turn_on(bet_type: str, phase: str) -> bool:
        """Determine if a bet can be turned on during the current phase."""
        _, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Use standardized lookup

        return bet_info.get("can_turn_on", False)  # ✅ Standardized access

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """Get the payout ratio for a bet."""
        _, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Use standardized lookup
        payout_key = bet_info["payout_ratio"]  # ✅ Extract payout type

        # ✅ Lookup payout table
        if payout_key in BET_PAYOUT:
            if "default" in BET_PAYOUT[payout_key]:  
                return BET_PAYOUT[payout_key]["default"]  # ✅ Case 1: Default payout
            if number is not None and number in BET_PAYOUT[payout_key]:  
                return BET_PAYOUT[payout_key][number]  # ✅ Case 2: Number-based payout

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
        """Determine if a bet has a vig (commission)."""
        _, bet_info = RulesEngine.find_bet_category(bet_type)  # ✅ Get correct bet rules
        return bet_info.get("has_vig", False)  # ✅ Use proper lookup
