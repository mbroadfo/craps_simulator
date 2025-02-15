# File: .\craps\visualizer.py

import matplotlib.pyplot as plt

class Visualizer:
    def __init__(self, stats):
        self.stats = stats

    def visualize_bankrolls(self):
        """Visualize player bankrolls over time."""
        plt.figure(figsize=(12, 6))

        # Plot each player's bankroll
        for player, bankrolls in self.stats.bankroll_history.items():
            # Ensure bankrolls and roll_numbers have the same length
            if len(bankrolls) != len(self.stats.roll_numbers):
                # Trim the longer list to match the shorter one
                min_length = min(len(bankrolls), len(self.stats.roll_numbers))
                bankrolls = bankrolls[:min_length]
                roll_numbers = self.stats.roll_numbers[:min_length]
            else:
                roll_numbers = self.stats.roll_numbers
            plt.plot(roll_numbers, bankrolls, label=player)

        # Add red vertical lines for 7-out events
        for roll in self.stats.seven_out_rolls:
            plt.axvline(x=roll, color='red', linestyle='--', alpha=0.5, label='7-Out' if roll == self.stats.seven_out_rolls[0] else "")

        # Add green dashed lines for point number rolls
        for roll in self.stats.point_number_rolls:
            plt.axvline(x=roll, color='green', linestyle=':', alpha=0.5, label='Point Number Rolled' if roll == self.stats.point_number_rolls[0] else "")

        # Set x-axis limits to start at 0 and end at the last roll
        last_roll = self.stats.roll_numbers[-1]
        plt.xlim(left=0, right=last_roll)

        # Customize x-axis ticks to include the last roll number
        x_ticks = list(range(0, last_roll + 1, 10))  # Major ticks every 10 rolls

        # Remove the next-to-last tick if it is within 3 of the last roll
        if len(x_ticks) >= 2 and (last_roll - x_ticks[-2]) <= 3:
            x_ticks.pop(-2)  # Remove the next-to-last tick

        # Add the last roll number if it's not already included
        if last_roll not in x_ticks:
            x_ticks.append(last_roll)

        plt.xticks(x_ticks)

        # Add labels and title
        plt.xlabel("Roll Number")
        plt.ylabel("Bankroll")
        plt.title("Player Bankrolls Over Time")
        plt.legend()
        plt.grid(True)
        plt.show()