from typing import Any


class HouseRules:
    """Class representing house rules for payouts, table limits, and session behavior."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.number_of_shooters: int = config.get("number_of_shooters", 3)
        self.dice_mode: str = config.get("dice_mode", "live")

        self.field_bet_payout_2: int = config.get("field_bet_payout_2", 2)
        self.field_bet_payout_12: int = config.get("field_bet_payout_12", 3)

        self.table_minimum: int = config.get("table_minimum", 10)
        self.table_maximum: int = config.get("table_maximum", 5000)

        self.come_odds_working_on_come_out: bool = config.get("come_odds_working_on_come_out", False)
        self.vig_on_win: bool = config.get("vig_on_win", True)

        self.leave_winning_bets_up: bool = config.get("leave_winning_bets_up", True)
        self.leave_bets_working: bool = config.get("leave_bets_working", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "number_of_shooters": self.number_of_shooters,
            "dice_mode": self.dice_mode,
            "field_bet_payout_2": self.field_bet_payout_2,
            "field_bet_payout_12": self.field_bet_payout_12,
            "table_minimum": self.table_minimum,
            "table_maximum": self.table_maximum,
            "come_odds_working_on_come_out": self.come_odds_working_on_come_out,
            "vig_on_win": self.vig_on_win,
            "leave_winning_bets_up": self.leave_winning_bets_up,
            "leave_bets_working": self.leave_bets_working,
        }
