from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from craps.bet import Bet
from craps.player import Player
from craps.game_state import GameState

if TYPE_CHECKING:
    from craps.table import Table

class BaseStrategy(ABC):
    """Abstract base class for all betting strategies."""

    def __init__(self, name: str):
        self.name = name  # Strategy name for tracking

    @abstractmethod
    def place_bets(self, game_state: GameState, player: Player, table: "Table") -> List[Bet]:
        """Determine which bets to place at the start of a roll."""
        pass

    def adjust_bets(self, game_state: GameState, player: Player, table: "Table") -> Optional[List[Bet]]:
        """Modify existing bets (e.g., adding odds, pressing bets)."""
        return None  # Default to no adjustments

    def remove_bets(self, game_state: GameState, player: Player, table: "Table") -> Optional[List[Bet]]:
        """Remove bets when necessary (e.g., conservative strategies)."""
        return None  # Default to no bet removal
    
    def turn_off_bets(self, game_state: GameState, player: Player, table: "Table") -> Optional[List[Bet]]:
        """Disable bets without removing them."""
        return None

    def turn_on_bets(self, game_state: GameState, player: Player, table: "Table") -> Optional[List[Bet]]:
        """Re-enable previously turned-off bets."""
        return None

    def on_new_shooter(self) -> None:
        """Optional hook called at the start of a new shooter."""
        pass

    def notify_payout(self, amount: int) -> None:
        """Optional hook called when a player wins a payout (excluding original bet)."""
        pass

    def notify_roll(self, game_state: "GameState", player: "Player", table: "Table") -> None:
        """Optional hook called after a roll is resolved."""
        pass
    
    def reset_shooter_state(self) -> None:
        """Optional hook for regression-based strategies to reset between modes."""
        pass

    def __str__(self) -> str:
        return f"{self.name} Strategy"
