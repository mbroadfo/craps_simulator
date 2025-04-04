# File: .\craps\visualizer.py

import matplotlib.pyplot as plt
from typing import Any

class Visualizer:
    def __init__(self, stats: Any) -> None:
        """
        Initialize the Visualizer.

        :param stats: The statistics object containing bankroll history and roll numbers.
        """
        self.stats = stats

    def visualize_bankrolls(self) -> None:
        """Visualize player bankrolls over time."""
        plt.figure(figsize=(12, 6))

        # Plot each player's bankroll
        for player, bankrolls in self.stats.bankroll_history.items():
            if len(bankrolls) != len(self.stats.roll_numbers):
                min_length = min(len(bankrolls), len(self.stats.roll_numbers))
                bankrolls = bankrolls[:min_length]
                roll_numbers = self.stats.roll_numbers[:min_length]
            else:
                roll_numbers = self.stats.roll_numbers
            plt.plot(roll_numbers, bankrolls, label=player)

        # Only show the legend label once per type
        seven_out_shown = False
        for roll in self.stats.seven_out_rolls:
            plt.axvline(
                x=roll,
                color='red',
                linestyle='--',
                alpha=0.5,
                label='7-Out' if not seven_out_shown else '_nolegend_'
            )
            seven_out_shown = True

        point_roll_shown = False
        for roll in self.stats.point_number_rolls:
            plt.axvline(
                x=roll,
                color='green',
                linestyle=':',
                alpha=0.5,
                label='Point Number Rolled' if not point_roll_shown else '_nolegend_'
            )
            point_roll_shown = True

        last_roll = self.stats.roll_numbers[-1]
        plt.xlim(left=0, right=last_roll)

        x_ticks = list(range(0, last_roll + 1, 10))
        if len(x_ticks) >= 2:
            next_to_last_tick = x_ticks[-2]
            if (last_roll - next_to_last_tick) <= 3 and (last_roll % 10 != 0):
                x_ticks.pop(-2)

        if last_roll not in x_ticks:
            x_ticks.append(last_roll)

        plt.xticks(x_ticks)
        plt.xlabel("Roll Number")
        plt.ylabel("Bankroll")
        plt.title("Player Bankrolls Over Time")
        plt.legend()
        plt.grid(True)
        plt.show()

