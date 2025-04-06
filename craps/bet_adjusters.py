"""
Bet Adjusters Module
=====================
This module defines a base class `BetAdjuster` and a growing library of concrete bet adjustment behaviors
used to manage post-roll bet modifications such as pressing, collecting, regressing, etc.

| Class Name                | Behavior Summary                                        |
|--------------------------|---------------------------------------------------------|
| `PressAdjuster`          | Full press after win (add full winnings to bet)         |
| `HalfPressAdjuster`      | Add half the winnings to the bet                        |
| `RegressAdjuster`        | Reduce the bet by a set number of units                 |
| `PowerPressAdjuster`     | Press full winnings plus one additional unit            |
| `PressAndCollectAdjuster`| Press a portion of the win and collect the rest         |
| `TakeDownAdjuster`       | Set bet status to inactive or remove from table         |
| `UnitPressAdjuster`      | Press in fixed increments (e.g., $6)                    |
| `TargetPressAdjuster`    | Keep pressing until target reached                      |
| `PressAcrossAdjuster`    | Press all place bets                                    |
| `PressInsideAdjuster`    | Press 5/6/8/9                                           |
| `PressOutsideAdjuster`   | Press 4/10                                              |
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from craps.bet import Bet
    from craps.table import Table
    from craps.rules_engine import RulesEngine


class BetAdjuster(ABC):
    """Abstract base class for bet adjustment behaviors."""

    @abstractmethod
    def adjust(self, bet: "Bet", table: "Table", rules_engine: "RulesEngine") -> None:
        pass


class PressAdjuster(BetAdjuster):
    """
    Fully presses the bet by adding the winnings to the current amount
    after a win. Assumes the bet has been resolved and won.
    """

    def adjust(self, bet: "Bet", table: "Table", rules_engine: "RulesEngine") -> None:
        if bet.status != "won":
            return

        bet.amount += bet.resolved_payout  # Add winnings to bet in-place
