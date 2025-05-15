ACTIVE_PLAYERS = {
    "Molly": ("3-Point Molly", False),
    "Dolly": ("3-Point Dolly", False),
    "Linus": ("Pass-Line", False),
    "Odd Linus": ("Pass-Line w/ Odds", False),
    "Fielder": ("Field", False),
    "Crosstopher": ("Iron Cross", True),
    "Insider": ("Inside", False),
    "All Boxes": ("Across", False),
    "Six-Eight": ("Place 68", False),
    "Layla": ("Lay Outside", False),
    "Blow Aces": ("Double Aces", False),
    "321-Blast": ("Three-Two-One", False),
    "Go Big": ("RegressHalfPress", False),
    "Hardy": ("HardwayHighway",False),
    "ATS": ("AllTallSmall", False),
}

NUM_SHOOTERS = 10

# Add a new configuration entry for session mode
DICE_MODE = "live"  # Options: "live" or "history"

# House Rules Configuration
HOUSE_RULES = {
    "field_bet_payout_2": (2, 1),  # 2:1 payout for 2
    "field_bet_payout_12": (3, 1),  # 3:1 payout for 12
    "table_minimum": 10,  # Minimum bet amount
    "table_maximum": 5000,  # Maximum bet amount
    "come_odds_working_on_come_out": False,  # Whether Come odds bets are working during the come-out roll
    "leave_bets_working": False,  # Non-contract bets follow the puck
    "leave_winning_bets_up": True,  # If it pays, it stays
}

DICE_TEST_PATTERNS = {
    "point_7_out": [
        (3, 3),  # point set
        (4, 1),  # random roll
        (5, 2),  # point = 7 out - DP wins
    ],
    "point_hit": [
        (3, 3),  # point = 6
        (6, 6),  # No change
        (3, 3),  # point hit → DP loses
    ],
    "front_line_winner": [
        (2, 5),  # front line winner
    ],

}
