# File: .\config.py

ACTIVE_PLAYERS = {
    "Pass-Line": False,
    "Pass-Line w/ Odds": False,
    "$44 Inside": False,
    "$54 Across": False,
    "Field": False,
    "Iron Cross": False,
    "3-Point Molly": True,
}

# Add a new configuration entry for session mode
SESSION_MODE = "live"  # Options: "live" or "history"

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
