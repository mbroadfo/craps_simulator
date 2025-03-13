from colorama import Fore, Style
from typing import Any, Tuple
from craps.player import Player
from craps.dice import Dice

class Shooter(Player):
    def __init__(self, name: str, initial_balance: int = 500, betting_strategy: Any = None, dice: Dice = None, play_by_play: Any = None):
        """
        Initialize a shooter.

        :param name: The name of the shooter.
        :param initial_balance: The initial bankroll of the shooter.
        :param betting_strategy: The betting strategy used by the shooter.
        :param dice: The Dice instance used for rolling.
        :param play_by_play: The PlayByPlay instance for logging game events.
        """
        super().__init__(name, initial_balance, betting_strategy, play_by_play)
        self.dice = dice if dice else Dice()
        self.current_roll_count = 0
        self.rolls_before_7_out = []

    def roll_dice(self) -> Tuple[int, int]:
        """
        Roll the dice and return the outcome.

        :return: A tuple representing the outcome of the dice roll.
        """
        outcome = self.dice.roll()
        self.current_roll_count += 1
        return outcome

    def reset_stats(self) -> None:
        """
        Reset the shooter's statistics for a new round.
        """
        self.current_roll_count = 0
        self.rolls_before_7_out = []
