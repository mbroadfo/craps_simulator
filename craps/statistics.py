## File: craps/statistics.py

from craps.log_manager import LogManager
import logging
class Statistics:
    def __init__(self, table_minimum, num_shooters, num_players):
        self.table_minimum = table_minimum
        self.num_shooters = num_shooters
        self.num_players = num_players
        self.num_rolls = 0
        self.total_house_win_loss = 0
        self.total_player_win_loss = 0
        self.player_bankrolls = []
        self.highest_bankroll = 0
        self.lowest_bankroll = float('inf')
        self.shooter_stats = {}

        # For visualization
        self.roll_numbers = [0]  # Start with roll 0
        self.bankroll_history = {}  # Track bankroll history for each player
        self.seven_out_rolls = []  # Track rolls where a 7-out occurs
        self.point_number_rolls = []  # Track rolls where a point number (4, 5, 6, 8, 9, 10) is rolled
        
    def initialize_bankroll_history(self, players):
        """Initialize bankroll history with the starting bankroll for each player."""
        for player in players:
            self.bankroll_history[player.name] = [player.balance]  # Roll 0: initial bankroll

    def merge(self, other_stats):
        """Merge statistics from another session."""
        self.num_rolls += other_stats.num_rolls
        self.total_house_win_loss += other_stats.total_house_win_loss
        self.total_player_win_loss += other_stats.total_player_win_loss
        self.player_bankrolls.extend(other_stats.player_bankrolls)
        self.highest_bankroll = max(self.highest_bankroll, other_stats.highest_bankroll)
        self.lowest_bankroll = min(self.lowest_bankroll, other_stats.lowest_bankroll)
        self.roll_numbers.extend(other_stats.roll_numbers)
        self.seven_out_rolls.extend(other_stats.seven_out_rolls)
        self.point_number_rolls.extend(other_stats.point_number_rolls)

        # Merge shooter stats
        for shooter_name, stats in other_stats.shooter_stats.items():
            if shooter_name not in self.shooter_stats:
                self.shooter_stats[shooter_name] = {
                    "points_rolled": 0,
                    "rolls_before_7_out": [],
                    "total_rolls": 0,
                }
            self.shooter_stats[shooter_name]["points_rolled"] += stats["points_rolled"]
            self.shooter_stats[shooter_name]["rolls_before_7_out"].extend(stats["rolls_before_7_out"])
            self.shooter_stats[shooter_name]["total_rolls"] += stats["total_rolls"]

        # Merge bankroll history
        for player, bankrolls in other_stats.bankroll_history.items():
            if player not in self.bankroll_history:
                self.bankroll_history[player] = []
            self.bankroll_history[player].extend(bankrolls)

    def update_rolls(self):
        """Increment the roll count."""
        self.num_rolls += 1
        self.roll_numbers.append(self.num_rolls)

    def update_player_bankrolls(self, players):
        """Update player bankrolls and track highest/lowest bankroll."""
        self.player_bankrolls = [player.balance for player in players]
        self.highest_bankroll = max(self.player_bankrolls)
        self.lowest_bankroll = min(self.player_bankrolls)

        # Track bankroll history for visualization
        for player in players:
            if player.name not in self.bankroll_history:
                self.bankroll_history[player.name] = []
            self.bankroll_history[player.name].append(player.balance)

    def record_seven_out(self):
        """Record the roll number where a 7-out occurs."""
        self.seven_out_rolls.append(self.num_rolls)
        
    def record_point_number_roll(self):
        """Record the roll number where a point number (4, 5, 6, 8, 9, 10) is rolled."""
        self.point_number_rolls.append(self.num_rolls)

    def visualize_bankrolls(self):
        """Visualize player bankrolls over time."""
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))

        # Plot each player's bankroll
        for player, bankrolls in self.bankroll_history.items():
            # Ensure bankrolls and roll_numbers have the same length
            if len(bankrolls) != len(self.roll_numbers):
                # Trim the longer list to match the shorter one
                min_length = min(len(bankrolls), len(self.roll_numbers))
                bankrolls = bankrolls[:min_length]
                roll_numbers = self.roll_numbers[:min_length]
            else:
                roll_numbers = self.roll_numbers
            plt.plot(roll_numbers, bankrolls, label=player)

        # Add red vertical lines for 7-out events
        for roll in self.seven_out_rolls:
            plt.axvline(x=roll, color='red', linestyle='--', alpha=0.5, label='7-Out' if roll == self.seven_out_rolls[0] else "")

        # Add green dotted lines for point number rolls
        for roll in self.point_number_rolls:
            plt.axvline(x=roll, color='green', linestyle=':', alpha=0.5, label='Point Number Rolled' if roll == self.point_number_rolls[0] else "")

        # Add labels and title
        plt.xlabel("Roll Number")
        plt.ylabel("Bankroll")
        plt.title("Player Bankrolls Over Time")
        plt.legend()
        plt.grid(True)
        plt.show()

    def update_shooter_stats(self, shooter):
        """Update shooter statistics."""
        if shooter.name not in self.shooter_stats:
            self.shooter_stats[shooter.name] = {
                "points_rolled": 0,
                "rolls_before_7_out": [],
                "total_rolls": 0,
            }
        self.shooter_stats[shooter.name]["points_rolled"] += shooter.points_rolled
        self.shooter_stats[shooter.name]["rolls_before_7_out"].append(shooter.rolls_before_7_out)
        self.shooter_stats[shooter.name]["total_rolls"] += shooter.current_roll_count

    def print_statistics(self):
        """Print the simulation statistics."""
        logging.info(LogManager.format_log_message("\n=== Simulation Statistics ==="))
        logging.info(LogManager.format_log_message(f"Table Minimum: ${self.table_minimum}"))
        logging.info(LogManager.format_log_message(f"Number of Shooters: {self.num_shooters}"))
        logging.info(LogManager.format_log_message(f"Number of Players: {self.num_players}"))
        logging.info(LogManager.format_log_message(f"Number of Rolls: {self.num_rolls}"))
        logging.info(LogManager.format_log_message(f"Total House Win/Loss: ${self.total_house_win_loss}"))
        logging.info(LogManager.format_log_message(f"Total Player Win/Loss: ${self.total_player_win_loss}"))
        logging.info(LogManager.format_log_message(f"Player Bankrolls: {self.player_bankrolls}"))
        logging.info(LogManager.format_log_message(f"Highest Player Bankroll: ${self.highest_bankroll}"))
        logging.info(LogManager.format_log_message(f"Lowest Player Bankroll: ${self.lowest_bankroll}"))

    def print_shooter_report(self):
        """Print a report summarizing each shooter's performance."""
        logging.info(LogManager.format_log_message("\n=== Shooter Performance Report ==="))
        for shooter_name, stats in self.shooter_stats.items():
            total_points_rolled = stats["points_rolled"]
            total_rolls = stats["total_rolls"]
            rolls_before_7_out = stats["rolls_before_7_out"]
            avg_rolls_before_7_out = sum(rolls_before_7_out) / len(rolls_before_7_out) if rolls_before_7_out else 0

            logging.info(LogManager.format_log_message(f"\nShooter: {shooter_name}"))
            logging.info(LogManager.format_log_message(f"  Total Points Rolled: {total_points_rolled}"))
            logging.info(LogManager.format_log_message(f"  Total Rolls: {total_rolls}"))
            logging.info(LogManager.format_log_message(f"  Average Rolls Before 7-Out: {avg_rolls_before_7_out:.2f}"))
            logging.info(LogManager.format_log_message(f"  Rolls Before 7-Out: {rolls_before_7_out}"))