from typing import Tuple, Optional

# ================================
# Bet Rules (Grouped by Category)
# ================================
BET_RULES = {
    "Line Bets": {
        "is_contract_bet": True,
        "valid_numbers": None,
        "Pass Line": {
            "linked_bet": "Pass Line Odds",
            "valid_phases": ["come-out"],
            "payout_ratio": "Even Money",
            "resolution": {
                "come_out_win": [7, 11],
                "come_out_lose": [2, 3, 12],
                "point_win": ["point_made"],
                "point_lose": [7]
            },
        },
        "Don't Pass": {
            "linked_bet": "Don't Pass Odds",
            "valid_phases": ["come-out"],
            "payout_ratio": "Even Money",
            "barred_numbers": [12],
            "resolution": {
                "come_out_win": [2, 3],
                "come_out_lose": [7, 11],
                "point_win": [7],
                "point_lose": ["point_made"]
            },
        },
        "Come": {
            "linked_bet": "Come Odds",
            "valid_phases": ["point"],
            "payout_ratio": "Even Money",
            "resolution": {
                "come_out_win": [7, 11],
                "come_out_lose": [2, 3, 12],
                "point_win": ["number_hit"],
                "point_lose": [7],
                "moves_on_roll": True,
            }
        },
        "Don't Come": {
            "linked_bet": "Don't Come Odds",
            "valid_phases": ["point"],
            "payout_ratio": "Even Money",
            "barred_numbers": [12],
            "resolution": {
                "come_out_win": [2, 3],
                "come_out_lose": [7, 11],
                "point_win": [7],
                "point_lose": ["number_hit"],
                "moves_on_roll": True,
            }
        },    },
    "Odds Bets": {
        "is_contract_bet": False,
        "valid_numbers": None,
        "Pass Line Odds": {
            "valid_phases": ["point"],
            "payout_ratio": "True Odds",
            "resolution": {
                "point_win": ["point_made"],
                "point_lose": [7],
            }
        },
        "Don't Pass Odds": {
            "valid_phases": ["point"],
            "payout_ratio": "Don't True Odds",
            "resolution": {
                "point_win": [7],
                "point_lose": ["point_made"],
            }
        },
        "Come Odds": {
            "valid_phases": ["point"],
            "payout_ratio": "True Odds",
            "resolution": {
                "point_win": ["number_hit"],
                "point_lose": [7],
            }
        },
        "Don't Come Odds": {
            "valid_phases": ["point"],
            "payout_ratio": "Don't True Odds",
            "resolution": {
                "point_win": [7],
                "point_lose": ["number_hit"],
            }
        },
    },
    "Place Bets": {
        "is_contract_bet": False,
        "valid_numbers": [4, 5, 6, 8, 9, 10],
        "Place": {
            "linked_bet": None,
            "valid_phases": ["point"],
            "payout_ratio": "Place Odds",
            "resolution": {
                "point_win": ["number_hit"],
                "point_lose": [7],
            }
        },
        "Don't Place": {
            "linked_bet": None,
            "valid_phases": ["point"],
            "payout_ratio": "Don't Place Odds",
            "resolution": {
                "point_win": [7],
                "point_lose": ["number_hit"],
            }
        },
        "Buy": {
            "linked_bet": None,
            "valid_phases": ["point"],
            "payout_ratio": "True Odds",
            "has_vig": True,
            "resolution": {
                "point_win": ["number_hit"],
                "point_lose": [7],
            }
        },
        "Lay": {
            "linked_bet": None,
            "valid_phases": ["point"],
            "payout_ratio": "Don't True Odds",
            "has_vig": True,
            "resolution": {
                "point_win": [7],
                "point_lose": ["number_hit"],
            }
        }
    },
    "Field Bets": {
        "is_contract_bet": False,
        "always_working": True,
        "valid_numbers": None,
        "Field": {
            "linked_bet": None,
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Field",
            "resolution": {
                "come_out_win": [2, 3, 4, 9, 10, 11, 12],
                "come_out_lose": [5, 6, 7, 8],
                "point_win": [2, 3, 4, 9, 10, 11, 12],
                "point_lose": [5, 6, 7, 8],
            }
        },
    },
    "Other Bets": {
        "is_contract_bet": False,
        "valid_numbers": None,
        "Proposition": {
            "valid_numbers": [2, 3, 7, 11, 12],
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Proposition",
            "resolution": {
                "come_out_win": ["number_hit"],
                "come_out_lose": ["any_other"], 
                "point_win": ["number_hit"],
                "point_lose": ["any_other"],
            },
        },
        "Hardways": {
            "valid_numbers": [4, 6, 8, 10],
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Hardways",
            "resolution": {
                "come_out_win": ["hardway_win"],
                "come_out_lose": ["hardway_lose"],
                "point_win": ["hardway_win"],
                "point_lose": ["hardway_lose"],
            },
        },
        "Hop": {
            "valid_numbers": [
                (1, 3), (1, 4), (1, 5), (1, 6),
                (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
                (3, 3), (3, 4), (3, 5), (3, 6),
                (4, 4), (4, 5), (4, 6),
                (5, 5)
            ],
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Hop",
            "resolution": {
                "come_out_win": ["hop_win"],
                "come_out_lose": ["hop_lose"],
                "point_win": ["hop_win"],
                "point_lose": ["hop_lose"],
            },
        },
    },
    "All Tall Small Bets": {
        "is_contract_bet": False,
        "valid_numbers": None,
        "All": {
            "linked_bet": None,
            "valid_phases": ["come-out"],
            "payout_ratio": "ATS-All",
            "resolution": {
                "win_condition": ["all_complete"],
                "lose_condition": [7],
            },
        },
        "Tall": {
            "linked_bet": None,
            "valid_phases": ["come-out"],
            "payout_ratio": "ATS-Tall",
            "resolution": {
                "win_condition": ["tall_complete"],
                "lose_condition": [7],
            },
        },
        "Small": {
            "linked_bet": None,
            "valid_phases": ["come-out"],
            "payout_ratio": "ATS-Small",
            "resolution": {
                "win_condition": ["small_complete"],
                "lose_condition": [7],
            },
        },
    },
    "Combo Bets": {
        "is_contract_bet": False,
        "always_working": True,
        "valid_numbers": None,
        "Horn": {
            "linked_bet": ["Proposition"],
            "composition": [2, 3, 11, 12],
            "payout_ratio": "Proposition",
        },
        "Horn High": {
            "linked_bet": ["Proposition"],
            "composition": [2, 3, 12, 11],
            "payout_ratio": "Proposition",
        },
        "World": {
            "linked_bet": ["Proposition"],
            "composition": [2, 3, 7, 11, 12],
            "payout_ratio": "World",
        },
    },
    "Segmented Field Bets": {
        "is_contract_bet": False,
        "valid_numbers": None,
        "Left Field": {
            "payout_ratio": "Left Field",
            "valid_phases": ["come-out", "point"],
            "resolution": {
                "come_out_win": [2, 3, 4],
                "come_out_lose": ["any_other"],
                "point_win": [2, 3, 4],
                "point_lose": ["any_other"],
            }
        },
        "Center Field": {
            "payout_ratio": "Center Field",
            "valid_phases": ["come-out", "point"],
            "resolution": {
                "come_out_win": [4, 9, 10],
                "come_out_lose": ["any_other"],
                "point_win": [4, 9, 10],
                "point_lose": ["any_other"],
            }
        },
        "Right Field": {
            "payout_ratio": "Right Field",
            "valid_phases": ["come-out", "point"],
            "resolution": {
                "come_out_win": [10, 11, 12],
                "come_out_lose": ["any_other"],
                "point_win": [10, 11, 12],
                "point_lose": ["any_other"],
            }
        },
    },
    "Midway Bets": {
        "is_contract_bet": False,
        "valid_numbers": None,
        "Midway": {
            "payout_ratio": "Midway",
            "valid_phases": ["come-out", "point"],
            "resolution": {
                "come_out_win": [6, 7, 8],
                "come_out_lose": ["any_other"],
                "point_win": [6, 7, 8],
                "point_lose": ["any_other"],
            }
        },
    },
    "Challenge Bets": {
        "is_contract_bet": True,
        "valid_numbers": None,
        "Point 7": {
            "payout_ratio": "Point 7",
            "valid_phases": ["come-out"],
            "resolution": {
                "win_condition": ["point_7out_next"],
                "lose_condition": ["natural_or_longer"]
            }
        },
        "7 Point 7": {
            "payout_ratio": "7 Point 7",
            "valid_phases": ["come-out"],
            "resolution": {
                "win_condition": ["co_7_or_point_7out"],
                "lose_condition": ["craps_or_extended"]
            }
        },
        "4 Rolls No 7": {
            "payout_ratio": "Even Money",
            "valid_phases": ["come-out", "point"],
            "resolution": {
                "win_condition": ["no_7_in_4_rolls"],
                "lose_condition": [7]
            }
        },
    },
    "Repeater Bets": {
        "is_contract_bet": False,
        "valid_numbers": [2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
        "Repeater": {
            "valid_phases": ["come-out", "point"],
            "parameterized": True,
            "payout_ratio_prefix": "Repeater",  # Combine with number dynamically
            "repeat_targets": {
                2: 2,
                3: 3,
                4: 4,
                5: 5,
                6: 6,
                8: 6,
                9: 5,
                10: 4,
                11: 3,
                12: 2
            },
            "resolution": {
                "win_condition": ["repeat_count_met"],
                "lose_condition": [7]
            }
        }
    }
}

# ================================
# Payout Ratios (Now a Function)
# ================================

BET_PAYOUT = {
    "Even Money": {
        "default": (1, 1)
    },
    "True Odds": {
        4: (2, 1),
        5: (3, 2),
        6: (6, 5),
        8: (6, 5),
        9: (3, 2),
        10: (2, 1),
    },
    "Place Odds": {
        4: (9, 5),
        5: (7, 5),
        6: (7, 6),
        8: (7, 6),
        9: (7, 5),
        10: (9, 5),
    },
    "Don't True Odds": {
        4: (1, 2),
        5: (2, 3),
        6: (5, 6),
        8: (5, 6),
        9: (2, 3),
        10: (1, 2),
    },
    "Don't Place Odds": {
        4: (5, 9),
        5: (5, 7),
        6: (6, 7),
        8: (6, 7),
        9: (5, 7),
        10: (5, 9),
    },
    "Field": {
        2: (2, 1),
        3: (1, 1),
        4: (1, 1),
        9: (1, 1),
        10: (1, 1),
        11: (1, 1),
        12: (3, 1),
    },
    "Proposition": {
        2: (30, 1),
        3: (15, 1),
        7: (4, 1),
        11: (15, 1),
        12: (30, 1),
    },
    "Hardways": {
        4: (7, 1),
        6: (9, 1),
        8: (9, 1),
        10: (7, 1),
    },
    "Hop": {
        (2, 2): (30, 1),
        (2, 3): (15, 1),
        (2, 4): (15, 1),
        (3, 3): (30, 1),
        (3, 4): (15, 1),
        (3, 5): (15, 1),
        (4, 4): (30, 1),
        (4, 5): (15, 1),
        (4, 6): (15, 1),
        (5, 5): (30, 1),
    },
    "ATS-All": (175, 1),        
    "ATS-Tall": (34, 1),
    "ATS-Small": (34, 1),
    "Left Field": (4, 1),
    "Center Field": (2, 1),
    "Right Field": (4, 1),
    "Midway": {
        (1, 5): (1, 1),  # Easy 6
        (2, 4): (1, 1),  # Easy 6
        (3, 3): (2, 1),  # Hard 6
        7: (1, 1),       # Any 7
        (2, 6): (1, 1),  # Easy 8
        (3, 5): (1, 1),  # Easy 8
        (4, 4): (2, 1),  # Hard 8
    },
    "Repeater": {
        2: (40, 1),
        3: (50, 1),
        4: (65, 1),
        5: (80, 1),
        6: (90, 1),
        8: (90, 1),
        9: (80, 1),
        10: (65, 1),
        11: (50, 1),
        12: (40, 1),
    }
}

ODDS_MULTIPLIERS = {
    "1x": {4: 1, 5: 1, 6: 1, 8: 1, 9: 1, 10: 1},
    "2x": {4: 2, 5: 2, 6: 2, 8: 2, 9: 2, 10: 2},
    "1x-2x-3x": {4: 1, 5: 2, 6: 3, 8: 3, 9: 2, 10: 1},
    "3x-4x-5x": {4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3},
    "10x": {4: 10, 5: 10, 6: 10, 8: 10, 9: 10, 10: 10},
    "20x": {4: 20, 5: 20, 6: 20, 8: 20, 9: 20, 10: 20},
    "100x": {4: 100, 5: 100, 6: 100, 8: 100, 9: 100, 10: 100},
}
