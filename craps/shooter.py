from craps.player import Player
from craps.dice import Dice

class Shooter(Player):
    def __init__(self, name, initial_balance=0, betting_strategy=None):
        super().__init__(name, initial_balance, betting_strategy)  # Pass betting_strategy to Player
        self.dice = Dice()

    def roll_dice(self):
        return self.dice.roll()

    def __str__(self):
        return f"Shooter: {self.name}, Balance: ${self.balance}"