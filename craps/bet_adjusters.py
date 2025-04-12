"""
Bet Adjusters Module
=====================
This module defines a base class `BetAdjuster` and a growing library of concrete bet adjustment behaviors
used to manage post-roll bet modifications such as pressing, collecting, regressing, etc.

| Class Name                | Behavior Summary                                        |
|--------------------------|---------------------------------------------------------|
| `PressAdjuster`          | Full press after win (add full winnings to bet)         |
| `RegressAdjuster`        | Reduce the bet by a set number of units                 |
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional
from enum import Enum

class PressStyle(Enum):
    HALF = "half"
    FULL = "full"
    POWER = "power"
    N_UNIT = "n_unit"

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
        # Determine the proper unit level based on hit count
        level_index = min(self.hit_count - 1, len(self.unit_levels) - 1)
        unit_multiplier = self.unit_levels[level_index]

        if not isinstance(bet.number, int):
            return  # Skip unsupported types

        unit_base = rules_engine.get_bet_unit("Place", bet.number)
        target_amount = unit_multiplier * unit_base

        if bet.amount > target_amount:
            bet.amount = target_amount
            
class PressAdjuster(BetAdjuster):
    def __init__(self, style: PressStyle = PressStyle.HALF, n_units: int = 1) -> None:
        self.style = style
        self.n_units = n_units

    def adjust(self, bet: "Bet", table: "Table", rules_engine: "RulesEngine") -> None:
        if bet.status != "won" or bet.resolved_payout == 0:
            return

        unit = bet.unit
        winnings = bet.resolved_payout
        additional = 0

        if self.style == PressStyle.HALF:
            additional = (winnings // 2) // unit * unit
        elif self.style == PressStyle.FULL:
            additional = (winnings // unit) * unit
        elif self.style == PressStyle.POWER:
            additional = ((winnings + unit - 1) // unit) * unit
        elif self.style == PressStyle.N_UNIT and self.n_units:
            additional = self.n_units * unit

        bet.amount += additional
