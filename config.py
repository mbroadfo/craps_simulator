# File: .\config.py

ACTIVE_PLAYERS = {
    "Pass-Line": False,
    "Pass-Line w/ Odds": True,
    "$44 Inside": False,
    "$54 Across": False,
    "Field": False,
    "Iron Cross": True,
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
}