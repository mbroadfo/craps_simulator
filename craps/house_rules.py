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

        # D6 availability flags: what this table offers. Default-open, so
        # every existing config behaves exactly as before. The felt renders
        # only what these enable; Table.validate_bet enforces the same set.
        self.ats_enabled: bool = config.get("ats_enabled", True)
        self.hardways_enabled: bool = config.get("hardways_enabled", True)
        self.hop_bets_enabled: bool = config.get("hop_bets_enabled", True)
        self.prop_bets_enabled: bool = config.get("prop_bets_enabled", True)

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
            "ats_enabled": self.ats_enabled,
            "hardways_enabled": self.hardways_enabled,
            "hop_bets_enabled": self.hop_bets_enabled,
            "prop_bets_enabled": self.prop_bets_enabled,
        }
