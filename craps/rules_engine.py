from typing import List, Optional, Dict, Any, Tuple
from craps.rules import BET_RULES, BET_PAYOUT
from craps.bet import Bet
from craps.house_rules import HouseRules

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def get_bet_rules(bet_type: str) -> dict:
        """Retrieve the rules for a given bet type."""
        for bets in BET_RULES.values():  # Ignore categories, just find the bet
            if bet_type in bets:
                return bets[bet_type]  # ✅ Return only the bet rules
        raise ValueError(f"Unknown bet type: {bet_type}")

    @staticmethod
    def get_linked_bet_type(bet_type: str) -> Optional[str]:
        """Returns the linked bet type, if any (e.g., Pass Line → Pass Line Odds)."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return bet_rules.get("linked_bet")

    @staticmethod
    def get_minimum_bet(bet_type: str, table_min: int, table_max: int) -> int:
        """Returns the correct minimum bet amount for a given bet type based on table rules."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval

        min_bet = 1  # All bets must be at least $1

        if "is_contract_bet" in bet_rules:  # Line & Field Bets
            min_bet = max(table_min, min_bet)
            return min(table_max, min_bet)

        if bet_type in ["Place", "Don't Place"] and bet_rules.get("number") in [6, 8]:
            return table_min + (table_min // 5)

        if bet_type in ["Pass Line Odds", "Don't Pass Odds", "Come Odds", "Don't Come Odds"]:
            return max(2, (table_min // 2) * 2)  # Ensure even numbers

        return min_bet  # Default minimum

    @staticmethod
    def create_bet(bet_type: str, amount: int, owner, number: Optional[int] = None, parent_bet: Optional[Bet] = None) -> Bet:
        """Create a bet based on the bet type."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval

        if not bet_rules:
            raise ValueError(f"Unknown bet type: {bet_type}")

        payout_ratio = None if bet_type == "Field" else RulesEngine.get_payout_ratio(bet_type, number)

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
    def can_make_bet(bet_type, phase):
        """Check if a bet type is allowed in the current phase."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return phase in bet_rules["valid_phases"]

    @staticmethod
    def can_remove_bet(bet_type: str, phase: str) -> bool:
        """Determine if a bet of the given type can be removed during the current phase."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval

        # Check if this specific bet is a contract bet
        is_contract_bet = bet_rules.get("is_contract_bet", False)

        # Check if the entire category is marked as contract bets
        category_contract_bet = BET_RULES.get("Line Bets", {}).get("is_contract_bet", False)

        # If either is True, the bet cannot be removed
        return not (is_contract_bet or category_contract_bet)


    @staticmethod
    def can_turn_on(bet_type: str, phase: str) -> bool:
        """Determine if a bet of the given type can be turned on during the current phase."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return bet_rules.get("can_turn_on", False)

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
        """Get the payout ratio for a bet based on its type and number (if applicable)."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        payout_key = bet_rules["payout_ratio"]

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
        bet_rules = RulesEngine.get_bet_rules(bet.bet_type)  # ✅ Unified retrieval
        resolution_rules = bet_rules["resolution"]
        phase_key = phase.replace("-", "_")

        # 🎯 **1. LINE BETS (Pass Line, Don't Pass, Come, Don't Come)**
        if bet.bet_type in BET_RULES["Line Bets"]:
            winning_numbers = resolution_rules.get(f"{phase_key}_win", [])
            losing_numbers = resolution_rules.get(f"{phase_key}_lose", [])

            # 🏆 **Check if the bet wins**
            if total in winning_numbers:
                bet.status = "won"
            elif total in losing_numbers:
                bet.status = "lost"

        ### 🎯 **2. FIELD BETS**
        elif bet.bet_type == "Field":
            if "in-field" in resolution_rules.get(f"{phase}_win", []):
                bet.status = "won"
                bet.number = total  # ✅ Assign the rolled number
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
            if "number_hit" in resolution_rules.get(f"{phase_key}_win", []) and total == bet.number:
                bet.status = "won"
            elif "any_other" in resolution_rules.get(f"{phase_key}_lose", []) and total != bet.number:
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
            if "hop_win" in resolution_rules.get(f"{phase}_win", []) and (sorted_dice == (bet.number, bet.number) or sorted_dice in BET_PAYOUT["Hop"]):
                bet.status = "won"
            elif "hop_lose" in resolution_rules.get(f"{phase}_lose", []) and (sorted_dice != (bet.number, bet.number) and sorted_dice not in BET_PAYOUT["Hop"]):
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
        """Determine if a bet of the given type has a vig (commission)."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return bet_rules.get("vig", False)
