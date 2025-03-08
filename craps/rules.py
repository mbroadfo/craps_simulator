from typing import Tuple, Optional

# ================================
# Bet Rules (Grouped by Category)
# ================================
BET_RULES = {
    "Line Bets": {
        "is_contract_bet": True,
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
        "Place": {
            "linked_bet": "Place Odds",
            "valid_phases": ["point"],
            "payout_ratio": "House Odds",
            "resolution": {
                "point_win": ["number_hit"],
                "point_lose": [7],
            }
        },
        "Don't Place": {
            "linked_bet": "Don't Place Odds",
            "valid_phases": ["point"],
            "payout_ratio": "Don't House Odds",
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
        }
    },
    "Proposition Bets": {
        "is_contract_bet": False,
        "Aces": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Proposition",
            "resolution": {
                "come_out_win": [2],
                "come_out_lose": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "point_win": [2],
                "point_lose": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            },
        },
        "Ace-Deuce": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Proposition",
            "resolution": {
                "come_out_win": [3],
                "come_out_lose": [2, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "point_win": [3],
                "point_lose": [2, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            },
        },
        "Yo (11)": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Proposition",
            "resolution": {
                "come_out_win": [11],
                "come_out_lose": [2, 3, 4, 5, 6, 7, 8, 9, 10, 12],
                "point_win": [11],
                "point_lose": [2, 3, 4, 5, 6, 7, 8, 9, 10, 12],
            },
        },
        "12": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Proposition",
            "resolution": {
                "come_out_win": [12],
                "come_out_lose": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "point_win": [12],
                "point_lose": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            },
        },
        "Any Seven": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Proposition",
            "resolution": {
                "come_out_win": [7],
                "come_out_lose": [2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
                "point_win": [7],
                "point_lose": [2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
            },
        },
        "Hardways": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Hardways",
            "resolution": {
                "point_win": {"hardway-win"},
                "point_lose": {"hardway-lose"}
            },
        },
        "Hop": {
            "valid_phases": ["come-out", "point"],
            "payout_ratio": "Hop",
            "resolution": {
                "point_win": {"number_hit"},
                "point_lose": {"numeber_miss"}
            },
        },
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
    "House Odds": {
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
    "Don't House Odds": {
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
        4: (30, 1),
        6: (30, 1),
        8: (30, 1),
        10: (30, 1),
    },
    "Hop": {
        4: (15, 1),
        5: (15, 1),  
        6: (15, 1),
        7: (15, 1),
        8: (15, 1),
        9: (15, 1),
        10: (15, 1),
        11: (15, 1),
        12: (15, 1),
    }
}

