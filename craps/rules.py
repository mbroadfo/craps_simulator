from typing import Tuple, Optional

# ================================
# Bet Rules (Grouped by Category)
# ================================
BET_RULES = {
    "Line Bets": {
        "Pass Line": {
            "linked_bet": "Pass Line Odds",
            "is_contract_bet": True,
            "valid_phases": ["come-out", "point"],
            "resolution_rule": "point_made",
        },
        "Pass Line Odds": {
            "linked_bet": None,
            "is_contract_bet": False,
            "valid_phases": ["point"],
            "resolution_rule": "point_made",
        },
        "Come": {
            "linked_bet": "Come Odds",
            "is_contract_bet": True,
            "valid_phases": ["point"],
            "resolution_rule": "come_moved",
        },
        "Come Odds": {
            "linked_bet": None,
            "is_contract_bet": False,
            "valid_phases": ["point"],
            "resolution_rule": "number_hit",
        },
    },
    "Place Bets": {
        "Place": {
            "linked_bet": "Place Odds",
            "is_contract_bet": False,
            "valid_phases": ["point"],
            "resolution_rule": "number_hit",
        },
        "Place Odds": {
            "linked_bet": None,
            "is_contract_bet": False,
            "valid_phases": ["point"],
            "resolution_rule": "number_hit",
        },
    },
    "Field Bets": {
        "Field": {
            "linked_bet": None,
            "is_contract_bet": False,
            "valid_phases": ["come-out", "point"],
            "resolution_rule": "field_roll",
        },
    }
}

# ================================
# Payout Ratios (Now a Function)
# ================================
ODDS_PAYOUT = {
    "True Odds": {
        4: (2, 1),
        5: (3, 2),
        6: (6, 5),
        8: (6, 5),
        9: (3, 2),
        10: (2, 1),
    },
    "House Odds": {
        4: (9, 5),
        5: (7, 5),
        6: (7, 6),
        8: (7, 6),
        9: (7, 5),
        10: (9, 5),
    },
    "Field Odds": {
        2: (2, 1),
        12: (3, 1),
    }
}

def get_payout_ratio(bet_type: str, number: Optional[int] = None) -> Tuple[int, int]:
    """
    Returns the payout ratio based on bet type and number (if applicable).
    """
    # Line Bets (Pass Line, Come)
    if bet_type in ["Pass Line", "Come"]:
        return (1, 1)
    
    # Line Bets - Odds
    if bet_type in ["Pass Line Odds", "Come Odds"]:
        return ODDS_PAYOUT["True Odds"].get(number, (1, 1))
    
    # Place Bets
    if bet_type in ["Place", "Place Odds"]:
        return ODDS_PAYOUT["House Odds"].get(number, (1, 1))

    # Field Bet Special Payouts
    if bet_type == "Field":
        return ODDS_PAYOUT["Field Odds"].get(number, (1, 1))

    # Default payout if unspecified
    return (1, 1)