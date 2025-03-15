from typing import List, Optional, Dict, Any, Tuple, Union
from craps.rules import BET_RULES, BET_PAYOUT
from craps.bet import Bet
from craps.house_rules import HouseRules

class RulesEngine:
    """A rules engine for handling bets based on the rules defined in rules.py."""

    @staticmethod
    def get_bet_rules(bet_type: str) -> Dict[str, Any]:
        """
        Retrieve the rules for a given bet type, including category-level attributes.
        
        :param bet_type: The type of bet (e.g., "Pass Line", "Field", "Hardways").
        :return: A dictionary containing the rules for the bet.
        """
        for category, bets in BET_RULES.items():
            if isinstance(bets, dict) and bet_type in bets:
                bet_rules = bets[bet_type].copy() if isinstance(bets[bet_type], dict) else {}
                category_rules = {k: v for k, v in bets.items() if not isinstance(v, dict)}
                return {**category_rules, **bet_rules}

        raise ValueError(f"Unknown bet type: {bet_type}")

    @staticmethod
    def get_linked_bet_type(bet_type: str) -> Optional[str]:
        """Returns the linked bet type, if any (e.g., Pass Line → Pass Line Odds)."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return bet_rules.get("linked_bet")

    @staticmethod
    def get_minimum_bet(bet_type: str, table: Any) -> int:
        """Returns the correct minimum bet amount for a given bet type based on table rules."""
        table_min = table.house_rules.table_minimum
        table_max = table.house_rules.table_maximum
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified rule retrieval

        # 🟢 **Base Minimum Bet: All bets must be at least $1**
        min_bet = 1

        # 🟢 **Line & Field Bets: Must be within table min & max**
        if bet_rules.get("is_contract_bet", False) or bet_type == "Field":
            min_bet = max(table_min, min_bet)  # Ensure at least table minimum
            return min(table_max, min_bet)  # Ensure it doesn't exceed table max

        # 🟢 **Prop, Hop, Hardways, Odds Bets: Can be as low as $1**
        elif bet_rules.get("valid_numbers") is not None and bet_type in ["Proposition", "Hardways", "Hop", "Odds"]:
            return min_bet  # No additional constraints

        # 🟢 **Place & Don't Place Bets: Special Case for 6 & 8**
        elif bet_type in ["Place", "Don't Place"] and bet_rules.get("valid_numbers") == [6, 8]:
            return table_min + (table_min // 5)  # Ensure correct payout increments

        # 🟢 **Odds on 5 & 9: Must be Even for Correct Payouts**
        elif bet_type in ["Pass Line Odds", "Don't Pass Odds", "Come Odds", "Don't Come Odds"] and bet_rules.get("valid_numbers") == [5, 9]:
            return max(2, (table_min // 2) * 2)  # Round up to the nearest even number

        return min_bet  # Default minimum bet

    @staticmethod
    def create_bet(bet_type: str, amount: int, owner: Any, number: Optional[Union[int, Tuple[int, int]]] = None, parent_bet: Optional[Bet] = None) -> Bet:
        """Create a bet based on the bet type."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval

        if not bet_rules:
            raise ValueError(f"Unknown bet type: {bet_type}")

        # ✅ Check if the number is valid for this bet type (supports both int and tuple)
        valid_numbers = bet_rules.get("valid_numbers")  # Can be None, a list of ints, or a list of tuples

        if valid_numbers is None and number is not None and bet_type not in ["Come Odds", "Don't Come Odds"]:
            raise ValueError(f"{bet_type} bet should not have a number")
        if valid_numbers and number not in valid_numbers:
            raise ValueError(f"Invalid number {number} for bet type {bet_type}")

        if valid_numbers:
            if isinstance(valid_numbers[0], tuple):  # ✅ If the rule expects tuples (e.g., Hop bets)
                if not isinstance(number, tuple) or number not in valid_numbers:
                    raise ValueError(f"Invalid tuple {number} for bet type {bet_type}")
            elif not isinstance(number, int) or number not in valid_numbers:  # ✅ If the rule expects a single number
                raise ValueError(f"Invalid number {number} for bet type {bet_type}")

        payout_ratio: Tuple[int, int] = RulesEngine.get_payout_ratio(bet_type, number) or (1, 1)

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
    def can_make_bet(bet_type: str, phase: str, number: Optional[int] = None) -> bool:
        """Check if a bet can be placed in the given phase and with a specific number."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Get the rules
        
        # ✅ Check valid phases (no change)
        if phase not in bet_rules["valid_phases"]:
            return False

        # ✅ Only check valid numbers **if the bet type has them defined**
        valid_numbers = bet_rules.get("valid_numbers")  # Get the valid numbers list
        if valid_numbers is not None and number is not None and number not in valid_numbers:
            return False  # ❌ Reject invalid numbers

        return True  # ✅ Bet is valid

    @staticmethod
    def can_turn_on(bet_type: str, phase: str) -> bool:
        """Determine if a bet of the given type can be turned on during the current phase."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return bet_rules.get("can_turn_on", False)
    
    @staticmethod
    def can_remove_bet(bet_type: str) -> bool:
        """
        Determine if a bet of the given type can be removed.
        Contract bets cannot be removed once placed.
        """
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Fetch all bet rules in one go
        return not bet_rules.get("is_contract_bet", False)  # ❌ Contract bets cannot be removed

    @staticmethod
    def get_payout_ratio(bet_type: str, number: Optional[Union[int, Tuple[int, int]]] = None) -> Tuple[int, int]:
        """Get the payout ratio for a bet based on its type and number (if applicable)."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)
        payout_key = bet_rules.get("payout_ratio")

        # Ensure payout_key exists and its value in BET_PAYOUT is a dictionary
        if payout_key in BET_PAYOUT:
            payout_data = BET_PAYOUT[payout_key]
            if isinstance(payout_data, dict):
                # Case 1: If no number is provided, return the default payout ratio
                if number is None:
                    return payout_data.get("default", (1, 1))

                # Case 2: If number is an integer (e.g., True Odds, Place Bets)
                if isinstance(number, int):
                    return payout_data.get(number, payout_data.get("default", (1, 1)))

                # Case 3: If number is a tuple (e.g., Hop bets)
                if isinstance(number, tuple):
                    return payout_data.get(number, payout_data.get("default", (1, 1)))

        raise ValueError(f"Invalid payout type {payout_key} for bet {bet_type} (number={number})")

    @staticmethod
    def resolve_bet(bet: Bet, dice_outcome: Tuple[int, int], phase: str, point: Optional[int]) -> int:
        """
        Resolves a bet based on the dice outcome, phase, and point.
        Uses a structured approach based on bet categories.
        """
        total = sum(dice_outcome)
        is_pair = dice_outcome[0] == dice_outcome[1]
        sorted_dice = tuple(sorted(dice_outcome))
        bet_rules = RulesEngine.get_bet_rules(bet.bet_type)  # ✅ Unified retrieval
        resolution_rules = bet_rules["resolution"]
        phase_key = phase.replace("-", "_")  # ✅ Normalize phase key

        # 🎯 **1. LINE BETS (Pass Line, Don't Pass, Come, Don't Come)**
        if bet_rules.get("is_contract_bet", False):  # ✅ Line bets use contract logic
            winning_numbers = resolution_rules.get(f"{phase_key}_win", [])
            losing_numbers = resolution_rules.get(f"{phase_key}_lose", [])

            # 🏆 **Come/Don't Come Special Case - Handle First Roll**
            if bet.bet_type in ["Come", "Don't Come"]:
                if bet.number is None:  # ✅ First roll for Come/Don't Come
                    if total in resolution_rules["come_out_win"]:
                        bet.status = "won"
                    elif total in resolution_rules["come_out_lose"]:
                        bet.status = "lost"
                    else:
                        bet.number = total  # ✅ Move the bet to a number
                else:  # ✅ Subsequent rolls after moving to a number
                    if total == bet.number:
                        bet.status = "won"
                    elif total == 7:
                        bet.status = "lost"
            
            # 🏆 **Regular Pass Line / Don't Pass Logic**
            elif total in winning_numbers:
                bet.status = "won"
            elif total in losing_numbers:
                bet.status = "lost"

        ### 🎯 **2. FIELD BETS**
        elif bet.bet_type == "Field":
            if "in-field" in resolution_rules.get(f"{phase_key}_win", []):
                bet.status = "won"
                bet.number = total  # ✅ Assign the rolled number
            elif "out-field" in resolution_rules.get(f"{phase_key}_lose", []):
                bet.status = "lost"

        ### 🎯 **3. PLACE, BUY, LAY BETS (Follow Rule Definitions)**
        elif bet.bet_type in ("Place", "Buy", "Lay"):
            winning_numbers = resolution_rules.get(f"{phase_key}_win", [])
            losing_numbers = resolution_rules.get(f"{phase_key}_lose", [])

            # ✅ Win if the rolled total matches the "number_hit" or is in "point_win"
            if "number_hit" in winning_numbers and total == bet.number:
                bet.status = "won"
            elif total in winning_numbers:  # ✅ Fully respects rules, includes Lay bet
                bet.status = "won"

            # ✅ Lose if total is in "point_lose"
            elif "point_lose" in losing_numbers and total == 7:
                bet.status = "lost"
            elif total in losing_numbers:
                bet.status = "lost"
                
        ### 🎯 **4. PROPOSITION BETS**
        elif bet.bet_type == "Proposition":
            if "number_hit" in resolution_rules.get(f"{phase_key}_win", []) and total == bet.number:
                bet.status = "won"
            elif "any_other" in resolution_rules.get(f"{phase_key}_lose", []) and total != bet.number:
                bet.status = "lost"

        ### 🎯 **5. HARDWAYS**
        elif bet.bet_type == "Hardways":
            if "hardway_win" in resolution_rules.get(f"{phase_key}_win", []):
                if total == bet.number and is_pair:
                    bet.status = "won"

            if "hardway_lose" in resolution_rules.get(f"{phase_key}_lose", []):
                if total == 7 or (total == bet.number and not is_pair):  # ✅ Easy way loses
                    bet.status = "lost"

        ### 🎯 **6. HOP BETS**
        elif bet.bet_type == "Hop":
            hop_payouts = BET_PAYOUT.get("Hop", {})

            if not isinstance(hop_payouts, dict):
                raise TypeError(f"Expected dict for Hop payouts, got {type(hop_payouts)}")

            # Normalize dice order for lookup
            sorted_dice = tuple(sorted(dice_outcome))

            # Ensure bet.number is a tuple and check both (X, Y) and (Y, X)
            if isinstance(bet.number, tuple):
                if sorted_dice == tuple(sorted(bet.number)):
                    bet.status = "won"
                else:
                    bet.status = "lost"

        ### 🎯 **7. ODDS BETS**
        elif bet.bet_type in ["Pass Line Odds", "Come Odds", "Don't Pass Odds", "Don't Come Odds"]:
            if bet.parent_bet and bet.parent_bet.status == "won":
                bet.status = "won"
            elif bet.parent_bet and bet.parent_bet.status == "lost":
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
            return 0  # ✅ No payout if the bet didn't win

        # Ensure the correct roll value is used for bets that depend on it (e.g., Field)
        number = roll if bet.bet_type == "Field" else bet.number

        # ✅ Field bets should only request payout if they actually won
        field_payouts = BET_PAYOUT.get("Field", {})

        if not isinstance(field_payouts, (dict, list, set)):
            raise TypeError(f"Expected dict, list, or set for Field payouts, got {type(field_payouts)}")

        if bet.bet_type == "Field" and number not in field_payouts:
            return 0  # ✅ If the number isn't a winning Field number, payout is $0

        payout_ratio = RulesEngine.get_payout_ratio(bet.bet_type, number)
        numerator, denominator = payout_ratio
        profit = (bet.amount * numerator) // denominator

        return profit

    @staticmethod
    def has_vig(bet_type: str) -> bool:
        """Determine if a bet of the given type has a vig (commission)."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)  # ✅ Unified retrieval
        return bet_rules.get("vig", False)
