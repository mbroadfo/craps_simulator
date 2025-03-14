from craps.player import Player
from craps.dice import Dice
from typing import Optional, List, Tuple, Any

class Shooter(Player):
    def __init__(
        self, 
        name: str, 
        initial_balance: int = 0, 
        betting_strategy: Optional[Any] = None, 
        dice: Optional[Dice] = None, 
        play_by_play: Optional[Any] = None
    ) -> None:
        """
        Initialize the shooter.

        :param name: The name of the shooter.
        :param initial_balance: The initial bankroll of the shooter.
        :param betting_strategy: The betting strategy used by the shooter.
        :param dice: An optional Dice instance for rolling dice.
        :param play_by_play: The PlayByPlay instance for logging.
        """
        super().__init__(name, initial_balance, betting_strategy, play_by_play)
        self.dice: Dice = dice if dice else Dice()  # Ensure Dice instance
        self.points_rolled: int = 0
        self.rolls_before_7_out: List[int] = []  # Explicit type annotation
        self.current_roll_count: int = 0  # Tracks rolls in the current turn

    def roll_dice(self) -> Tuple[int, int]:
        """
        Roll the dice and update shooter statistics.

        :return: A tuple representing the dice roll (e.g., (3, 4)).
        """
        outcome: List[int] = self.dice.roll()
        self.current_roll_count += 1

        if len(outcome) != 2:
            raise ValueError(f"Dice roll must return exactly two values, got: {outcome}")

        return outcome[0], outcome[1]  # Ensure exactly (int, int)

    def reset_stats(self) -> None:
        """
        Reset shooter statistics for a new turn.
        """
        self.points_rolled = 0
        self.rolls_before_7_out = []
        self.current_roll_count = 0
