from craps.player import Player
from craps.dice import Dice

class Shooter(Player):
    def __init__(self, name, initial_balance=0, betting_strategy=None, dice=None, play_by_play=None):
        super().__init__(
            name,
            initial_balance=initial_balance,
            betting_strategy=betting_strategy,
            play_by_play=play_by_play
        )
        self.dice = dice if dice else Dice()
        self.points_rolled = 0  # Number of times the shooter rolled the point
        self.rolls_before_7_out = 0  # Number of rolls before 7-ing out
        self.current_roll_count = 0  # Tracks rolls in the current turn

    def roll_dice(self):
        """Roll the dice and update shooter statistics."""
        outcome = self.dice.roll()
        self.current_roll_count += 1
        return outcome

    def reset_stats(self):
        """Reset shooter statistics for a new turn."""
        self.points_rolled = 0
        self.rolls_before_7_out = 0
        self.current_roll_count = 0