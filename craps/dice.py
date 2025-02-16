import csv
import random

class Dice:
    def __init__(self, roll_history_file=None):
        """
        Initialize the Dice class.
        
        :param roll_history_file: Path to a CSV file containing roll history. If None, rolls are random.
        """
        self.values = [1, 1]
        self.roll_history_file = roll_history_file
        self.roll_history = []
        self.current_roll_index = 0

        if self.roll_history_file:
            self._load_roll_history()

    def _load_roll_history(self):
        """Load roll history from a CSV file."""
        with open(self.roll_history_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert dice and total to integers
                dice = [int(die) for die in row["dice"].strip('[]').split(', ')]
                total = int(row["total"])
                shooter_num = int(row["shooter_num"])
                self.roll_history.append({
                    "dice": dice,
                    "total": total,
                    "shooter_num": shooter_num
                })

    def roll(self):
        """Roll the dice. If roll history is loaded, use the next roll from the history."""
        if self.roll_history:
            if self.current_roll_index >= len(self.roll_history):
                raise IndexError("No more rolls in the history.")
            roll = self.roll_history[self.current_roll_index]
            self.values = roll["dice"]
            self.current_roll_index += 1
            return roll["dice"]
        else:
            # Generate random rolls if no history is loaded
            self.values = [random.randint(1, 6), random.randint(1, 6)]
            return self.values