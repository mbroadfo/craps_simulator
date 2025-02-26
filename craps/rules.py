# File: .\craps\rules.py

# ==================================================
# Table 1: Bet Behavior
# ==================================================

BET_BEHAVIOR = {
    "Pass Line": {
        "is_contract_bet": True,
        "linked_bet": "Pass Line Odds",
        "valid_phases": ["come-out", "point"],
        "come-out": {
            "can_bet": True,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": [7, 11],
            "losing": [2, 3, 12],
            "other_action": "Sets the Point",
        },
        "point": {
            "can_bet": False,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Point"],
            "losing": [7],
            "other_action": "No Change",
        },
    },
    "Pass Line Odds": {
        "is_contract_bet": True,
        "linked_bet": None,
        "valid_phases": ["point"],
        "come-out": {
            "can_bet": False,
            "can_remove": "Must Remove",
            "can_turn_on": "Must Remove",
            "winning": None,
            "losing": None,
            "other_action": None,
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Point"],
            "losing": [7],
            "other_action": "No Change",
        },
    },
    "Come": {
        "is_contract_bet": True,
        "linked_bet": "Come Odds",
        "valid_phases": ["point"],
        "come-out": {
            "can_bet": False,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": [7, 11],
            "losing": [2, 3, 12],
            "other_action": "No Change",
        },
        "point": {
            "can_bet": True, 
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
        },
    },
    "Come Odds": {
        "is_contract_bet": False,
        "linked_bet": None,
        "valid_phases": ["point"],
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": None,
            "losing": None,
            "other_action": None,
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
        },
    },
    "Place": {
        "is_contract_bet": False, 
        "linked_bet": "Place Odds",
        "valid_phases": ["point"],
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
        },
    },
    "Place Odds": {
        "is_contract_bet": False,
        "linked_bet": None,
        "valid_phases": ["point"],
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
        },
    },
    "Field": {
        "is_contract_bet": True,
        "linked_bet": None,
        "valid_phases": ["come-out", "point"],
        "come-out": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": [2, 3, 4, 9, 10, 11, 12],
            "losing": [5, 6, 7, 8],
            "other_action": "No Change",
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": [2, 3, 4, 9, 10, 11, 12],
            "losing": [5, 6, 7, 8],
            "other_action": "No Change",
        },
    },
    # Add similar rules for other bet types...
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