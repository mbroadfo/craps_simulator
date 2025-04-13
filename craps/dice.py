import csv
import random
import os
from typing import Optional, List, Dict, Tuple, cast
from collections import deque

class Dice:
    def __init__(self, roll_history_file: Optional[str] = None) -> None:
        """
        Initialize the Dice class.
        
        :param roll_history_file: Path to a CSV file containing roll history. If None, rolls are random.
        """
        self.values: Tuple[int, int] = (1, 1)  # Ensure this is a fixed-size tuple
        self.roll_history_file: Optional[str] = roll_history_file
        self.roll_history: List[Dict[str, int | Tuple[int, int]]] = []
        self.current_roll_index: int = 0
        self.forced_rolls: deque[Tuple[int, int]] = deque()
        self.current_roll_index = 0

        if self.roll_history_file:
            self._load_roll_history()

    def _load_roll_history(self) -> None:
        """Load roll history from a CSV file."""
        if not self.roll_history_file:
            return  # Prevent passing None to open()

        if not os.path.exists(self.roll_history_file):
            raise FileNotFoundError(f"Roll history file '{self.roll_history_file}' not found.")

        with open(self.roll_history_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert dice and total to proper types
                dice_list = row["dice"].strip('[]').split(', ')
                if len(dice_list) != 2:
                    raise ValueError(f"Invalid dice format in roll history: {row['dice']}")
                
                dice: Tuple[int, int] = (int(dice_list[0]), int(dice_list[1]))  # Ensure exactly two values
                total: int = int(row["total"])
                shooter_num: int = int(row["shooter_num"])
                self.roll_history.append({
                    "dice": dice,
                    "total": total,
                    "shooter_num": shooter_num
                })

    def roll(self) -> Tuple[int, int]:
        """Forced Rolls used for testing"""
        if self.forced_rolls:
            self.values = self.forced_rolls.popleft()
            return self.values
        """Roll the dice. If roll history is loaded, use the next roll from the history."""
        if self.roll_history:
            if self.current_roll_index >= len(self.roll_history):
                raise IndexError("No more rolls in the history.")
            roll = self.roll_history[self.current_roll_index]
            dice = cast(Tuple[int, int], roll["dice"])
            if len(dice) != 2:
                raise ValueError(f"Invalid dice format in roll history: {roll['dice']}")

            self.values = dice  # Ensure it's a valid (int, int) tuple
            self.current_roll_index += 1
        else:
            """ Generate random rolls if no history is loaded """
            self.values = (random.randint(1, 6), random.randint(1, 6))  # Ensure it's a tuple
        
        return self.values
