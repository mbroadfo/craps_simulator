# File: .\craps\statistics.py

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

    def update_rolls(self):
        """Increment the roll count."""
        self.num_rolls += 1

    def update_player_bankrolls(self, players):
        """Update player bankrolls and track highest/lowest bankroll."""
        self.player_bankrolls = [player.balance for player in players]
        self.highest_bankroll = max(self.player_bankrolls)
        self.lowest_bankroll = min(self.player_bankrolls)

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
        print("\n=== Simulation Statistics ===")
        print(f"Table Minimum: ${self.table_minimum}")
        print(f"Number of Shooters: {self.num_shooters}")
        print(f"Number of Players: {self.num_players}")
        print(f"Number of Rolls: {self.num_rolls}")
        print(f"Total House Win/Loss: ${self.total_house_win_loss}")
        print(f"Total Player Win/Loss: ${self.total_player_win_loss}")
        print(f"Player Bankrolls: {self.player_bankrolls}")
        print(f"Highest Player Bankroll: ${self.highest_bankroll}")
        print(f"Lowest Player Bankroll: ${self.lowest_bankroll}")

    def print_shooter_report(self):
        """Print a report summarizing each shooter's performance."""
        print("\n=== Shooter Performance Report ===")
        for shooter_name, stats in self.shooter_stats.items():
            total_points_rolled = stats["points_rolled"]
            total_rolls = stats["total_rolls"]
            rolls_before_7_out = stats["rolls_before_7_out"]
            avg_rolls_before_7_out = sum(rolls_before_7_out) / len(rolls_before_7_out) if rolls_before_7_out else 0

            print(f"\nShooter: {shooter_name}")
            print(f"  Total Points Rolled: {total_points_rolled}")
            print(f"  Total Rolls: {total_rolls}")
            print(f"  Average Rolls Before 7-Out: {avg_rolls_before_7_out:.2f}")
            print(f"  Rolls Before 7-Out: {rolls_before_7_out}")