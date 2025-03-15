from typing import List, Optional, Tuple
from craps.dice import Dice
from craps.player import Player

class Shooter:
    def __init__(self, name: str, initial_balance: int = 1000, dice: Optional[Dice] = None) -> None:
        """
        Initialize a Shooter.

        :param name: The name of the shooter.
        :param initial_balance: The shooter's starting balance.
        :param dice: The Dice instance to use for rolling.
        """
        self.name: str = name  # ✅ Ensure the shooter has a name
        self.balance: int = initial_balance
        self.dice: Dice = dice if dice else Dice()
        self.current_roll_count: int = 0
        self.rolls_before_7_out: List[Tuple[int, int]] = []  # Track rolls before 7-out

    def roll_dice(self) -> Tuple[int, int]:
        """
        Roll the dice and track the outcome.

        :return: A tuple representing the dice roll (e.g., (3, 4)).
        """
        outcome = self.dice.roll()
        self.rolls_before_7_out.append(outcome)
        self.current_roll_count += 1
        return outcome

    def reset_shooter(self) -> None:
        """
        Reset the shooter's roll count for a new round.
        """
        self.current_roll_count = 0
        self.rolls_before_7_out.clear()
