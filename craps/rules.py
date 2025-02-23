# File: .\craps\rules.py

# ==================================================
# Table 1: Bet Behavior
# ==================================================

BET_BEHAVIOR = {
    "Pass Line": {
        "come-out": {
            "can_bet": True,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": [7, 11],
            "losing": [2, 3, 12],
            "other_action": "Sets the Point",
            "linked_bet": "Pass Line Odds",  # Pass Line Odds is linked to Pass Line
        },
        "point": {
            "can_bet": False,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Point"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Pass Line Odds",  # Pass Line Odds is linked to Pass Line
        },
    },
    "Pass Line Odds": {
        "come-out": {
            "can_bet": False,
            "can_remove": "Must Remove",
            "can_turn_on": "Must Remove",
            "winning": None,
            "losing": None,
            "other_action": None,
            "linked_bet": None,  # No linked bet for Pass Line Odds
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Point"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Pass Line Odds
        },
    },
    "Place": {
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Place Odds",  # Place Odds is linked to Place
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Place Odds",  # Place Odds is linked to Place
        },
    },
    "Place Odds": {
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Place Odds
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Place Odds
        },
    },
    "Buy": {
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Buy bets
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Buy bets
        },
    },
    "Come": {
        "come-out": {
            "can_bet": False,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "Moves to Number",  # Come bet moves to the number rolled
            "linked_bet": "Come Odds",  # Come Odds is linked to Come
        },
        "point": {
            "can_bet": True,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Come Odds",  # Come Odds is linked to Come
        },
    },
    "Come Odds": {
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Come Odds
        },
        "point": {
            "can_bet": "Come Moves",
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,  # No linked bet for Come Odds
        },
    },
    "Field": {
        "come-out": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": True,
            "winning": [2, 3, 4, 9, 10, 11, 12],
            "losing": [5, 6, 7, 8],
            "other_action": None,
            "linked_bet": None,  # No linked bet for Field bets
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": [2, 3, 4, 9, 10, 11, 12],
            "losing": [5, 6, 7, 8],
            "other_action": None,
            "linked_bet": None,  # No linked bet for Field bets
        },
    },
}

# ==================================================
# Table 2: Bet Payout
# ==================================================

BET_PAYOUT = {
    "Pass Line": {"payout_ratio": (1, 1), "vig": False},
    "Pass Line Odds": {"payout_ratio": "True Odds", "vig": False},
    "Place": {"payout_ratio": "House Odds", "vig": False},
    "Place Odds": {"payout_ratio": "True Odds", "vig": False},
    "Buy": {"payout_ratio": "True Odds", "vig": True},
    "Come": {"payout_ratio": (1, 1), "vig": False},
    "Come Odds": {"payout_ratio": "True Odds", "vig": False},
    "Field": {"payout_ratio": (1, 1), "vig": False},
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
}