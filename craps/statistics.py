# File: craps/statistics.py

import logging
from typing import List, Dict, Any, Optional

class Statistics:
    def __init__(self, table_minimum: int, num_shooters: int, num_players: int) -> None:
        self.table_minimum: int = table_minimum
        self.num_shooters: int = num_shooters
        self.num_players: int = num_players
        self.num_rolls: int = 0
        self.total_house_win_loss: int = 0
        self.total_player_win_loss: int = 0
        self.player_bankrolls: List[int] = []
        self.highest_bankroll: int = 0
        self.lowest_bankroll: float = float('inf')
        self.shooter_stats: Dict[int, Dict[str, Any]] = {}
        self.player_stats: Dict[str, Dict[str, Any]] = {}
        self.shooter: Optional[Any] = None
        self.shooter_num: Optional[int] = None

        # For visualization
        self.roll_numbers: List[int] = [0]  # Start with roll 0
        self.bankroll_history: Dict[str, List[int]] = {}  # Track bankroll history for each player
        self.seven_out_rolls: List[int] = []  # Track rolls where a 7-out occurs
        self.point_number_rolls: List[int] = []  # Track rolls where a point number (4, 5, 6, 8, 9, 10) is rolled
        
    def initialize_player_stats(self, players: List[Any]) -> None:
        """Initialize player statistics with their starting bankroll."""
        for player in players:
            self.player_stats[player.name] = {
                "initial_bankroll": player.balance,
                "final_bankroll": player.balance,
                "net_win_loss": 0,
            }
            
    def update_player_stats(self, players: List[Any]) -> None:
        """Update player statistics at the end of the session."""
        for player in players:
            if player.name in self.player_stats:
                self.player_stats[player.name]["final_bankroll"] = player.balance
                self.player_stats[player.name]["net_win_loss"] = (
                    player.balance - self.player_stats[player.name]["initial_bankroll"]
                )
                
    def print_player_statistics(self) -> None:
        """Print player-specific statistics."""
        logging.info("\n=== Player Performance Report ===")
        for player_name, stats in self.player_stats.items():
            net_win_loss = stats["net_win_loss"]
            result = "Won" if net_win_loss >= 0 else "Lost"
            logging.info(f"\nPlayer: {player_name}")
            logging.info(f"  Initial Bankroll: ${stats['initial_bankroll']}")
            logging.info(f"  Final Bankroll: ${stats['final_bankroll']}")
            logging.info(f"  Net Win/Loss: ${net_win_loss} ({result})")
    
    def set_shooter(self, shooter: Any, shooter_num: int) -> None:
        """Set the current shooter and their turn number."""
        self.shooter = shooter
        self.shooter_num = shooter_num  # Track the shooter's turn number
        if shooter_num not in self.shooter_stats:
            self.shooter_stats[shooter_num] = {
                "points_rolled": 0,
                "rolls_before_7_out": [],
                "total_rolls": 0,
            }
            
    def initialize_bankroll_history(self, players: List[Any]) -> None:
        """Initialize bankroll history with the starting bankroll for each player."""
        for player in players:
            self.bankroll_history[player.name] = [player.balance]  # Roll 0: initial bankroll

    def merge(self, other_stats: "Statistics") -> None:
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

    def update_rolls(self) -> None:
        """Increment the roll count."""
        self.num_rolls += 1
        self.roll_numbers.append(self.num_rolls)

    def update_win_loss(self, bet: Any) -> None:
        """
        Update the house and player win/loss based on the resolved bet.

        :param bet: The resolved bet.
        """
        if bet.status == "won":
            payout = bet.payout()
            self.total_house_win_loss -= payout
            self.total_player_win_loss += payout
        elif bet.status == "lost":
            self.total_house_win_loss += bet.amount
            self.total_player_win_loss -= bet.amount
    
    def update_player_bankrolls(self, players: List[Any]) -> None:
        """Update player bankrolls and track highest/lowest bankroll."""
        self.player_bankrolls = [player.balance for player in players]
        self.highest_bankroll = max(self.player_bankrolls)
        self.lowest_bankroll = min(self.player_bankrolls)

        for player in players:
            if player.name not in self.bankroll_history:
                self.bankroll_history[player.name] = []
            self.bankroll_history[player.name].append(player.balance)

    def record_seven_out(self) -> None:
        """Record the roll number where a 7-out occurs."""
        self.seven_out_rolls.append(self.num_rolls)
        if self.shooter:
            self.shooter_stats[self.shooter_num]["rolls_before_7_out"].append(self.shooter.current_roll_count)
            self.shooter.current_roll_count = 0
        
    def record_point_number_roll(self) -> None:
        """Record the roll number where a point number (4, 5, 6, 8, 9, 10) is rolled."""
        self.point_number_rolls.append(self.num_rolls)
        if self.shooter:
            self.shooter_stats[self.shooter_num]["points_rolled"] += 1

    def update_shooter_stats(self, shooter: Any) -> None:
        """Update shooter statistics."""
        if self.shooter_num not in self.shooter_stats:
            self.shooter_stats[self.shooter_num] = {
                "points_rolled": 0,
                "rolls_before_7_out": [],
                "total_rolls": 0,
            }
        self.shooter_stats[self.shooter_num]["total_rolls"] = shooter.current_roll_count
        self.shooter_stats[self.shooter_num]["rolls_before_7_out"].append(shooter.rolls_before_7_out)

    def print_statistics(self) -> None:
        """Print the simulation statistics."""
        logging.info("\n=== Simulation Statistics ===")
        logging.info(f"Table Minimum: ${self.table_minimum}")
        logging.info(f"Number of Shooters: {self.num_shooters}")
        logging.info(f"Number of Players: {self.num_players}")
        logging.info(f"Number of Rolls: {self.num_rolls}")
        logging.info(f"Total House Win/Loss: ${self.total_house_win_loss}")
        logging.info(f"Total Player Win/Loss: ${self.total_player_win_loss}")
        logging.info(f"Player Bankrolls: {self.player_bankrolls}")
        logging.info(f"Highest Player Bankroll: ${self.highest_bankroll}")
        logging.info(f"Lowest Player Bankroll: ${self.lowest_bankroll}")

    def print_shooter_report(self):
        """Print a report summarizing each shooter's performance."""
        logging.info("\n=== Shooter Performance Report ===")
        for shooter_num, stats in self.shooter_stats.items():
            total_points_rolled = stats["points_rolled"]
            total_rolls = stats["total_rolls"]
            rolls_before_7_out = stats["rolls_before_7_out"]
            avg_rolls_before_7_out = sum(rolls_before_7_out) / len(rolls_before_7_out) if rolls_before_7_out else 0
