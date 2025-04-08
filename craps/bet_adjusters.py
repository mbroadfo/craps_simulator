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
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from craps.bet import Bet
    from craps.table import Table
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player

class BetAdjuster(ABC):
    """Abstract base class for bet adjustment behaviors."""

    @abstractmethod
    def adjust(self, bet: "Bet", table: "Table", rules_engine: "RulesEngine") -> None:
        pass
    
    def on_new_shooter(self, game_state: "GameState", player: "Player", table: "Table") -> None:
        """Optional hook called after every roll."""
        pass

    def notify_roll(self, game_state: "GameState", player: "Player", table: "Table") -> None:
        """Optional hook called after every roll."""
        pass

    def notify_payout(self, amount: int) -> None:
        """Optional hook called when a player wins a payout (not including original bet)."""
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

class RegressAdjuster(BetAdjuster):
    """
    Adjusts a Place bet downward based on a regression progression.

    Given a unit progression (e.g. [20, 10, 5]) and a current hit count,
    this adjuster determines the proper unit level and adjusts the bet
    amount accordingly—rounded to standard Place bet units.

    Example:
    - If hit_count = 1 and unit_levels = [20, 10, 5], unit = 10
    - Bet on 6 → target = 10 * 6 = $60
    - Bet on 5 → target = 10 * 5 = $50
    """

    def __init__(self, unit_levels: List[int], hit_count: int) -> None:
        self.unit_levels = unit_levels
        self.hit_count = hit_count

    def adjust(self, bet: "Bet", table: "Table", rules_engine: "RulesEngine") -> None:
        # Determine the regression level based on hit count
        level = min(self.hit_count, len(self.unit_levels) - 1)
        unit = self.unit_levels[level]

        # Calculate proper target amount
        if bet.number in [6, 8]:
            target_amount = unit * 6
        elif bet.number in [5, 9]:
            target_amount = unit * 5
        else:
            return  # Not a supported Place number

        if bet.amount > target_amount:
            bet.amount = target_amount
            
class HalfPressAdjuster(BetAdjuster):
    def adjust(self, bet: "Bet", table: "Table", rules_engine: "RulesEngine") -> None:
        if bet.status != "won" or bet.resolved_payout == 0:
            return

        number = bet.number
        if number in [6, 8]:
            unit = 6
        elif number in [5, 9]:
            unit = 5
        else:
            return  # Not an inside Place bet

        half_press = bet.resolved_payout // 2
        additional = (half_press // unit) * unit  # Round down to nearest multiple
        bet.amount += additional

