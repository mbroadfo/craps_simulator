HOUSE_RULES_SCHEMA = {
    "number_of_shooters": {
        "label": "Number of Shooters",
        "type": "number",
        "default": 10,
        "min": 1,
        "max": 100
    },
    "table_minimum": {
        "label": "Table Minimum",
        "type": "number",
        "default": 10,
        "options": [5, 10, 15, 25, 50, 100]
    },
    "table_maximum": {
        "label": "Table Maximum",
        "type": "number",
        "default": 5000,
        "min": 1000,
        "max": 10000
    },
    "max_odds": {
       "label": "Max Odds",
       "type": "select",
       "default": "3x-4x-5x",
       "options": [
           "1x",
           "2x",
           "3x",
           "0x-1x-2x",
           "1x-2x-3x",
           "2x-3x-4x",
           "3x-4x-5x",
           "10x",
           "20x",
           "100x",
       ]
    },
    "field_bet_payout_2": {
        "label": "Field 2 Pays",
        "type": "select",
        "default": "Double",
        "options": ["Double", "Triple"],
        "values": {
            "Double": [2, 1],
            "Triple": [3, 1]
        }
    },
    "field_bet_payout_12": {
        "label": "Field 12 Pays",
        "type": "select",
        "default": "Triple",
        "options": ["Double", "Triple"],
        "values": {
            "Double": [2, 1],
            "Triple": [3, 1]
        }
    },
    "come_odds_working_on_come_out": {
        "label": "Come Odds Working",
        "type": "boolean",
        "default": False
    },
    "leave_bets_working": {
        "label": "Leave Bets Working",
        "type": "boolean",
        "default": False
    },
    "leave_winning_bets_up": {
        "label": "Winning Bets Stay",
        "type": "boolean",
        "default": True
    },
    "dice_mode": {
        "label": "Dice Mode",
        "type": "select",
        "default": "live",
        "options": ["live", "history"]
    }
}