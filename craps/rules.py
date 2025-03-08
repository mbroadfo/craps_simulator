# File: .\craps\rules.py

# ==================================================
# Table 1: Bet Rules
# ==================================================

BET_RULES = {
    "Pass Line": {
        "linked_bet": "Pass Line Odds",
        "is_contract_bet": True,
        "valid_phases": ["come-out", "point"],
        "after_roll": {
            "come-out": {"winning": [7, 11], "losing": [2, 3, 12], "other_action": "Sets the Point"},
            "point": {"winning": ["Point"], "losing": [7], "other_action": "No Change"},
        },
    },
    "Pass Line Odds": {
        "linked_bet": None,
        "is_contract_bet": False,
        "valid_phases": ["point"],
        "after_roll": {
            "point": {"winning": ["Point"], "losing": [7], "other_action": "No Change"},
        },
    },
    "Come": {
        "linked_bet": "Come Odds",
        "is_contract_bet": True,
        "valid_phases": ["point"],
        "after_roll": {
            "come-out": {"winning": [7, 11], "losing": [2, 3, 12], "other_action": "No Change"},
            "point": {"winning": ["Number"], "losing": [7], "other_action": "No Change"},
        },
    },
    "Come Odds": {
        "linked_bet": None,
        "is_contract_bet": False,
        "valid_phases": ["point"],
        "after_roll": {
            "point": {"winning": ["Number"], "losing": [7], "other_action": "No Change"},
        },
    },
    "Place": {
        "linked_bet": "Place Odds",
        "is_contract_bet": False,
        "valid_phases": ["point"],
        "after_roll": {
            "come-out": {"winning": ["Number"], "losing": [7], "other_action": "No Change"},
            "point": {"winning": ["Number"], "losing": [7], "other_action": "No Change"},
        },
    },
    "Place Odds": {
        "linked_bet": None,
        "is_contract_bet": False,
        "valid_phases": ["point"],
        "after_roll": {
            "come-out": {"winning": ["Number"], "losing": [7], "other_action": "No Change"},
            "point": {"winning": ["Number"], "losing": [7], "other_action": "No Change"},
        },
    },
    "Field": {
        "linked_bet": None,
        "is_contract_bet": False,
        "valid_phases": ["come-out", "point"],
        "after_roll": {
            "come-out": {"winning": [2, 3, 4, 9, 10, 11, 12], "losing": [5, 6, 7, 8], "other_action": "No Change"},
            "point": {"winning": [2, 3, 4, 9, 10, 11, 12], "losing": [5, 6, 7, 8], "other_action": "No Change"},
        },
    },
}

# ==================================================
# Table 2: Bet Payout
# ==================================================

BET_PAYOUT = {
    "Pass Line": {"payout_ratio": (1, 1), "vig": False},
    "Pass Line Odds": {"payout_ratio": "True Odds", "vig": False},
    "Come": {"payout_ratio": (1, 1), "vig": False},
    "Come Odds": {"payout_ratio": "True Odds", "vig": False},
    "Place": {"payout_ratio": "House Odds", "vig": False},
    "Place Odds": {"payout_ratio": "True Odds", "vig": False},
    "Field": {"payout_ratio": "Field Odds", "vig": False},
}

# ==================================================
# Table 3: Odds Payout
# ==================================================

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
        2: (2, 1),  # 2:1 payout for 2
        12: (3, 1),  # 3:1 payout for 12
        # Other winning numbers (3, 4, 9, 10, 11) default to 1:1
    }
}