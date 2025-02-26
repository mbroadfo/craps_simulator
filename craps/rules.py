# File: .\craps\rules.py

# ==================================================
# Table 1: Bet Behavior
# ==================================================

BET_BEHAVIOR = {
    # Pass Line and Pass Line Odds (already defined)
    "Pass Line": {
        "come-out": {
            "can_bet": True,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": [7, 11],
            "losing": [2, 3, 12],
            "other_action": "Sets the Point",
            "linked_bet": "Pass Line Odds",
        },
        "point": {
            "can_bet": False,
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Point"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Pass Line Odds",
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
            "linked_bet": None,
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Point"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,
        },
    },
    # Place Bet
    "Place": {
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Place Odds",
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Place Odds",
        },
    },
    # Place Odds
    "Place Odds": {
        "come-out": {
            "can_bet": False,
            "can_remove": True,
            "can_turn_on": True,
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,
        },
        "point": {
            "can_bet": True,  # Allow Place Odds bets during the point phase
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,
        },
    },
    # Come Bet
    "Come": {
        "come-out": {
            "can_bet": False,  # Come bets cannot be placed during the come-out phase
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": [7, 11],
            "losing": [2, 3, 12],
            "other_action": "Moves to Number",
            "linked_bet": "Come Odds",
        },
        "point": {
            "can_bet": True,  # Come bets can be placed during the point phase
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": "Come Odds",
        },
    },
    # Come Odds Bet
    "Come Odds": {
        "come-out": {
            "can_bet": False,  # Come Odds bets cannot be placed during the come-out phase
            "can_remove": False,
            "can_turn_on": "Always On",
            "winning": None,
            "losing": None,
            "other_action": None,
            "linked_bet": None,
        },
        "point": {
            "can_bet": True,  # Come Odds bets can be placed during the point phase
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": ["Number"],
            "losing": [7],
            "other_action": "No Change",
            "linked_bet": None,
        },
    },
    # Field Bet
    "Field": {
        "come-out": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": [2, 3, 4, 9, 10, 11, 12],  # Winning numbers for Field bet
            "losing": [5, 6, 7, 8],  # Losing numbers for Field bet
            "other_action": "No Change",
            "linked_bet": None,
        },
        "point": {
            "can_bet": True,
            "can_remove": True,
            "can_turn_on": "Always On",
            "winning": [2, 3, 4, 9, 10, 11, 12],  # Winning numbers for Field bet
            "losing": [5, 6, 7, 8],  # Losing numbers for Field bet
            "other_action": "No Change",
            "linked_bet": None,
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
    "Come": {"payout_ratio": (1, 1), "vig": False},
    "Come Odds": {"payout_ratio": "True Odds", "vig": False},
    "Field": {"payout_ratio": "Field Odds", "vig": False},  # Add Field bet payout
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