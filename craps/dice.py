import random

class Dice:
    def __init__(self):
        self.values = [1, 1]

    def roll(self):
        self.values = [random.randint(1, 6), random.randint(1, 6)]
        return self.values