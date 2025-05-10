from typing import Optional, Dict, Any, Tuple, Union, TYPE_CHECKING
from craps.rules import BET_RULES, BET_PAYOUT
from craps.bet import Bet
from craps.game_state import GameState

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
    def get_minimum_bet(bet_type: str, table: Any, number: int | None = None) -> int:
        """Returns the correct minimum bet amount for a given bet type based on table rules."""
        table_min = table.house_rules.table_minimum
        table_max = table.house_rules.table_maximum
        bet_rules = RulesEngine.get_bet_rules(bet_type) 
        
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
        elif bet_type in ["Place", "Buy", "Lay"]:
            if number in [6, 8]:
                return table_min + (table_min // 5)  # $12 for $10 table minimum
            else:
                return table_min

        # 🟢 **Odds on 5 & 9: Must be Even for Correct Payouts**
        elif bet_type in ["Pass Line Odds", "Don't Pass Odds", "Come Odds", "Don't Come Odds"] and bet_rules.get("valid_numbers") == [5, 9]:
            return max(2, (table_min // 2) * 2)  # Round up to the nearest even number

        return min_bet  # Default minimum bet

    @staticmethod
    def get_bet_unit(bet_type: str, number: Optional[Union[int, Tuple[int, int]]]) -> int:
        if bet_type == "Place":
            if number in [6, 8]:
                return 6
            elif number in [5, 9, 4, 10]:
                return 5
            else:
                raise ValueError(f"Invalid Place number: {number}")
        # Add additional bet types as needed
        return 1  # Default fallback

    @staticmethod
    def validate_bet_phase(bet: Bet, phase: str) -> tuple[bool, Optional[str]]:
        """
        Check if the bet is valid for the current game phase.

        :param bet: The bet to validate.
        :param phase: The current game phase.
        :return: (is_valid, message) — True if valid, otherwise a reason.
        """
        if phase not in bet.valid_phases:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet cannot be placed during the {phase} phase."
        return True, None
    
    @staticmethod
    def validate_bet(
        bet: Bet,
        phase: str,
        table_minimum: int,
        table_maximum: int,
        game_state: Optional[GameState] = None
    ) -> tuple[bool, Optional[str]]:
        
        # 🚫 Prevent betting in the wrong phase
        if phase not in bet.valid_phases:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet cannot be placed during the {phase} phase."

        # 🚫 Prevent bets smaller than table minimum
        bets_with_table_minimums = ["Pass", "Don't Pass", "Come", "Don't Come", "Place", "Buy", "Lay"]
        minimum = table_minimum if bet.bet_type in bets_with_table_minimums else 1
        if bet.amount < minimum:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet (${bet.amount}) is below table minimum (${minimum})."

        # 🚫 Prevent bets larger than table maximum
        if bet.amount > table_maximum:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet (${bet.amount}) exceeds table maximum (${table_maximum})."

        # 🚫 Prevent bets of invalid size
        unit = bet.unit or 1
        if bet.amount % unit != 0:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet of ${bet.amount} must be in units of ${unit}."

        # 🚫 Prevent ATS re-bet after completion
        if game_state:
            if bet.bet_type == "All" and game_state.all_completed:
                return False, f"{bet.owner.name} cannot remake All bet — already completed this shooter."
            if bet.bet_type == "Tall" and game_state.tall_completed:
                return False, f"{bet.owner.name} cannot remake Tall bet — already completed this shooter."
            if bet.bet_type == "Small" and game_state.small_completed:
                return False, f"{bet.owner.name} cannot remake Small bet — already completed this shooter."

        return True, None

    @staticmethod
    def create_bet(bet_type: str, amount: int, owner: Any, number: Optional[Union[int, Tuple[int, int]]] = None, parent_bet: Optional[Bet] = None) -> Bet:
        """Create a bet based on the bet type."""
        bet_rules = RulesEngine.get_bet_rules(bet_type)

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
            vig=bet_rules.get("has_vig", False),
            unit = RulesEngine.get_bet_unit(bet_type, number),
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

        if payout_key in BET_PAYOUT:
            payout_data = BET_PAYOUT[payout_key]

            # 🟢 Case 1: Flat ratio (ATS, Even Money)
            if isinstance(payout_data, tuple) and len(payout_data) == 2:
                return payout_data
            elif isinstance(payout_data, dict):
                # Case 2: If no number is provided, return the default payout ratio
                if number is None:
                    return payout_data.get("default", (1, 1))

                # Case 3: If number is an integer (e.g., True Odds, Place Bets)
                if isinstance(number, int):
                    return payout_data.get(number, payout_data.get("default", (1, 1)))

                # Case 4: If number is a tuple (e.g., Hop bets)
                if isinstance(number, tuple):
                    return payout_data.get(number, payout_data.get("default", (1, 1)))

        raise ValueError(f"Invalid payout type {payout_key} for bet {bet_type} (number={number})")

    @staticmethod
    def resolve_bet(bet: Bet, dice_outcome: Tuple[int, int], game_state: GameState) -> int:
        """
        Resolves a bet based on the dice outcome, phase, and point.
        Uses a structured approach based on bet categories.
        """
        total = sum(dice_outcome)
        is_pair = dice_outcome[0] == dice_outcome[1]
        sorted_dice = tuple(sorted(dice_outcome))
        phase = game_state.phase
        point = game_state.point
        phase_key = phase.replace("-", "_")

        bet_rules = RulesEngine.get_bet_rules(bet.bet_type)
        resolution_rules = bet_rules["resolution"]
        winning_numbers = resolution_rules.get(f"{phase_key}_win", [])
        losing_numbers = resolution_rules.get(f"{phase_key}_lose", [])

        # ✅ Only resolve ACTIVE bets
        if bet.status != "active":
            return 0
        
        # 🎯 **1. LINE BETS (Pass Line, Don't Pass, Come, Don't Come)**
        if bet_rules.get("is_contract_bet", False):
            # 🏆 **Come/Don't Come Special Case - Handle First Roll**
            if bet.bet_type in ["Come", "Don't Come"]:
                if bet.number is None:  # Come bet in come-out mode
                    come_out_win = resolution_rules.get("come_out_win", [])
                    come_out_lose = resolution_rules.get("come_out_lose", [])
                    barred = bet_rules.get("barred_numbers", [])

                    if total in come_out_win:
                        bet.status = "won"
                    elif total in come_out_lose:
                        bet.status = "lost"
                    elif total in barred:
                        pass # Bet is barred on this number
                    else:
                        bet.number = total  # Bet moved to number
                else:  # Come bet in point mode
                    if "number_hit" in winning_numbers and total == bet.number:
                        bet.status = "won"
                    elif total in winning_numbers:
                        bet.status = "won"
                    elif "number_hit" in losing_numbers and total == bet.number:
                        bet.status = "lost"
                    elif total in losing_numbers:
                        bet.status = "lost"

            elif bet.bet_type in ("Pass Line", "Don't Pass"):  # Pass Line / Don't Pass logic
                # Win conditions
                if "number_hit" in winning_numbers and bet.number is not None and total == bet.number:
                    bet.status = "won"
                elif "point_made" in winning_numbers and point is not None and total == point:
                    bet.status = "won"
                elif total in winning_numbers:
                    bet.status = "won"
                # Loss conditions
                elif "number_hit" in losing_numbers and bet.number is not None and total == bet.number:
                    bet.status = "lost"
                elif "point_made" in losing_numbers and point is not None and total == point:
                    bet.status = "lost"
                elif total in losing_numbers:
                    bet.status = "lost"
            
        ### 🎯 **2. FIELD BETS**
        elif bet.bet_type == "Field":
            if total in winning_numbers:
                bet.status = "won"
                bet.number = total
            elif total in losing_numbers:
                bet.status = "lost"

        ### 🎯 **3. PLACE, BUY, LAY BETS (Follow Rule Definitions)**
        elif bet.bet_type in ("Place", "Buy", "Lay"):
            winning_numbers = resolution_rules.get(f"{phase_key}_win", [])
            losing_numbers = resolution_rules.get(f"{phase_key}_lose", [])

            # ✅ Win if the rolled total matches the "number_hit" or is in "point_win"
            if "number_hit" in winning_numbers and total == bet.number:
                bet.status = "won"
            elif total in winning_numbers:
                bet.status = "won"

            # ✅ Lose if total is in "point_lose"
            elif "number_hit" in losing_numbers and total == bet.number:
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

                # 🧠 Assign number based on parent for correct payout ratio
                if bet.number is None:
                    if bet.parent_bet.bet_type == "Pass Line":
                        bet.number = point  # Set to the current point
                    elif bet.parent_bet.bet_type == "Come":
                        bet.number = bet.parent_bet.number  # Set to the come number

            elif bet.parent_bet and bet.parent_bet.status == "lost":
                bet.status = "lost"

        ### 🎯 **7. ALL TALL SMALL BETS**
        elif bet.bet_type in ("All", "Tall", "Small"):  #. All / Tall / Small
            if game_state is None:
                raise RuntimeError("GameState is required for ATS bet resolution.")
            total = sum(dice_outcome)
            
            # Lose immediately on 7
            if total == 7:
                bet.status = "lost"
            elif bet.bet_type == "All" and game_state.all_completed:
                bet.status = "won"
            elif bet.bet_type == "Tall" and game_state.tall_completed:
                bet.status = "won"
            elif bet.bet_type == "Small" and game_state.small_completed:
                bet.status = "won"
        else:
            raise ValueError(f"Unknown contract bet: {bet.bet_type}")

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

    @staticmethod
    def get_odds_multiplier(odds_type: str, point: Optional[int] = None) -> Optional[int]:
        """Retrieve the odds multiplier from the rules based on the specified odds type and point number."""
        from craps.rules import ODDS_MULTIPLIERS  # Ensure we're always using the latest rules
        
        if odds_type not in ODDS_MULTIPLIERS:
            raise ValueError(f"Unknown odds type: {odds_type}")

        multiplier_data = ODDS_MULTIPLIERS[odds_type]

        if isinstance(multiplier_data, dict):
            return multiplier_data.get(point) if point is not None else None
        return multiplier_data  # Return the multiplier directly if it's a flat value

    @staticmethod
    def is_odds_eligible(bet: Bet, game_state: GameState) -> bool:
        if not bet.linked_bet:
            return False

        base_type = bet.linked_bet.bet_type
        if base_type == "Pass Line":
            return game_state.phase == "point"
        if base_type == "Come":
            return game_state.phase == "point" and bet.linked_bet.number is not None
        if base_type == "Don't Pass":
            return game_state.phase == "point"
        if base_type == "Don't Come":
            return game_state.phase == "point" and bet.linked_bet.number is not None
        return False
