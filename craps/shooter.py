from typing import Optional
from craps.player import Player
from craps.dice import Dice

class Shooter(Player):
    def __init__(self, name: str, initial_balance: int = 0, betting_strategy: Optional[object] = None, 
                 dice: Optional[Dice] = None, play_by_play: Optional[object] = None) -> None:
        """
        Initialize the shooter.

        :param name: The name of the shooter.
        :param initial_balance: The initial bankroll of the shooter.
        :param betting_strategy: The betting strategy used by the shooter.
        :param dice: The dice instance for rolling.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        """
        super().__init__(
            name,
            initial_balance=initial_balance,
            betting_strategy=betting_strategy,
            play_by_play=play_by_play
        )
        self.dice: Dice = dice if dice else Dice()
        self.points_rolled: int = 0  # Number of times the shooter rolled the point
        self.rolls_before_7_out: int = 0  # Number of rolls before 7-ing out
        self.current_roll_count: int = 0  # Tracks rolls in the current turn

    def roll_dice(self) -> list[int]:
        """Roll the dice and update shooter statistics."""
        outcome = self.dice.roll()
        self.current_roll_count += 1
        return outcome

    def reset_stats(self) -> None:
        """Reset shooter statistics for a new turn."""
        self.points_rolled = 0
        self.rolls_before_7_out = 0
        self.current_roll_count = 0