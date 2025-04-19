import logging
from typing import List, Dict, Any, Optional

class Statistics:
    def __init__(self, table_minimum: int, num_shooters: int, num_players: int) -> None:
        self.table_minimum: int = table_minimum
        self.num_shooters: int = num_shooters
        self.num_players: int = num_players
        self.session_rolls: int = 0
        self.total_amount_bet: int = 0
        self.total_amount_won: int = 0
        self.total_amount_lost: int = 0
        self.session_highest_bankroll: int = 0
        self.session_lowest_bankroll: int = 1_000_000
        self.total_house_win_loss: int = 0
        self.total_player_win_loss: int = 0
        self.player_bankrolls: List[int] = []
        self.highest_bankroll: int = 0
        self.lowest_bankroll: int = 1_000_000
        self.max_table_risk: int = 0
        self.total_sevens: int = 0
        self.shooter_stats: Dict[int, Dict[str, Any]] = {}
        self.player_stats: Dict[str, Dict[str, Any]] = {}
        self.shooter: Optional[Any] = None
        self.shooter_num: Optional[int] = None
        self.roll_history: List[Dict[str, Any]] = []
        self.session_high_roller: Optional[tuple[str, str, int]] = None  # (player_name, strategy_name, profit)
        self.session_low_roller: Optional[tuple[str, str, int]] = None   # (player_name, strategy_name, loss)

        # For visualization
        self.roll_numbers: List[int] = [0]  # Start with roll 0
        self.bankroll_history: Dict[str, List[int]] = {}  # Track bankroll history for each player
        self.at_risk_history: Dict[str, List[int]] = {}  # Track at_risk history for each player
        self.seven_out_rolls: List[int] = []  # Track rolls where a 7-out occurs
        self.point_number_rolls: List[int] = []  # Track rolls where a point number (4, 5, 6, 8, 9, 10) is rolled
        
    def initialize_player_stats(self, players: List[Any]) -> None:
        """Initialize player statistics with their starting bankroll."""
        for player in players:
            self.player_stats[player.name] = {
                "initial_bankroll": player.balance,
                "final_bankroll": player.balance,
                "net_win_loss": 0,
                "bets_settled": 0,
                "bets_won": 0,
                "bets_lost": 0,
                "highest_bankroll": player.balance,
                "lowest_bankroll": player.balance,
            }
            
    def update_player_stats(self, players: List[Any]) -> None:
        """Update player statistics at the end of the session."""
        for player in players:
            if player.name in self.player_stats:
                self.player_stats[player.name]["final_bankroll"] = player.balance
                self.player_stats[player.name]["net_win_loss"] = (
                    player.balance - self.player_stats[player.name]["initial_bankroll"]
                )
    
    def set_shooter(self, shooter: Any, shooter_num: int) -> None:
        """Set the current shooter and their turn number."""
        self.shooter = shooter
        self.shooter_num = shooter_num  # Track the shooter's turn number
        if shooter_num not in self.shooter_stats:
            self.shooter_stats[shooter_num] = {
                "points_rolled": 0,
                "rolls_before_7_out": [],
                "shooter_rolls": 0,
            }
            
    def initialize_bankroll_history(self, players: List[Any]) -> None:
        """Initialize bankroll history with the starting bankroll for each player."""
        for player in players:
            self.bankroll_history[player.name] = [player.balance]  # Roll 0: initial bankroll

    def initialize_at_risk_history(self, players: List[Any]) -> None:
        """Initialize at_risk history as zero for each player."""
        for player in players:
            self.at_risk_history[player.name] = [0]  # Roll 0: initial risk

    def merge(self, other_stats: "Statistics") -> None:
        """Merge statistics from another session."""
        self.session_rolls += other_stats.session_rolls
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
                    "shooter_rolls": 0,
                }
            self.shooter_stats[shooter_name]["points_rolled"] += stats["points_rolled"]
            self.shooter_stats[shooter_name]["rolls_before_7_out"].extend(stats["rolls_before_7_out"])
            self.shooter_stats[shooter_name]["shooter_rolls"] += stats["shooter_rolls"]

        # Merge bankroll history
        for player, bankrolls in other_stats.bankroll_history.items():
            if player not in self.bankroll_history:
                self.bankroll_history[player] = []
            self.bankroll_history[player].extend(bankrolls)
        
        # Merge at_risk history
        for player, at_risks in other_stats.at_risk_history.items():
            if player not in self.at_risk_history:
                self.at_risk_history[player] = []
            self.at_risk_history[player].extend(at_risks)

    def update_rolls(self, total: Optional[int] = None, table_risk: Optional[int] = None) -> None:
        """Increment the roll count and optionally record roll total and table risk."""
        self.session_rolls += 1
        self.roll_numbers.append(self.session_rolls)
        
        if total is not None:
            self.last_roll_total = total

        if total == 7:
            self.total_sevens += 1

        if table_risk is not None:
            self.max_table_risk = max(self.max_table_risk, table_risk)

    def update_win_loss(self, bet: Any) -> None:
        """
        Update the house and player win/loss based on the resolved bet.

        :param bet: The resolved bet.
        """
        if bet.status in ("won", "lost"):
            self.total_amount_bet += bet.amount

            player_stats = self.player_stats.get(bet.owner.name)
            if player_stats:
                player_stats["bets_settled"] += 1
                if bet.status == "won":
                    self.total_amount_won += bet.payout()
                    player_stats["bets_won"] += 1
                elif bet.status == "lost":
                    self.total_amount_lost += bet.amount
    
    def update_player_bankrolls(self, players: List[Any]) -> None:
        """Update player bankrolls and track highest/lowest bankroll."""
        self.player_bankrolls = [player.balance for player in players]
        self.highest_bankroll = max(self.player_bankrolls)
        self.lowest_bankroll = min(self.player_bankrolls)

        for player in players:
            if player.name not in self.bankroll_history:
                self.bankroll_history[player.name] = []
            self.bankroll_history[player.name].append(player.balance)
            
            if player.name in self.player_stats:
                stats = self.player_stats[player.name]
                stats["highest_bankroll"] = max(stats["highest_bankroll"], player.balance)
                stats["lowest_bankroll"] = min(stats["lowest_bankroll"], player.balance)
            
            if player.balance > self.session_highest_bankroll:
                self.session_highest_bankroll = player.balance
            if player.balance < self.session_lowest_bankroll:
                self.session_lowest_bankroll = player.balance

    def update_player_risk(self, players: List[Any], table: Any) -> None:
        """Update the amount at risk for each player this roll."""
        for player in players:
            at_risk = sum(b.amount for b in table.bets if b.owner == player and b.status == "active")
            if player.name not in self.at_risk_history:
                self.at_risk_history[player.name] = []
            self.at_risk_history[player.name].append(at_risk)

    def record_seven_out(self) -> None:
        """Record the roll number where a 7-out occurs."""
        self.seven_out_rolls.append(self.session_rolls)
        if self.shooter and self.shooter_num is not None:  # Ensure shooter_num is an int
            if self.shooter_num not in self.shooter_stats:
                self.shooter_stats[self.shooter_num] = {
                    "points_rolled": 0,
                    "rolls_before_7_out": [],
                    "shooter_rolls": 0,
                }
            self.shooter_stats[self.shooter_num]["rolls_before_7_out"].append(self.shooter.current_roll_count)
            self.shooter.current_roll_count = 0
        
    def record_point_number_roll(self) -> None:
        """Record the roll number where a point number (4, 5, 6, 8, 9, 10) is rolled."""
        self.point_number_rolls.append(self.session_rolls)
        if self.shooter and self.shooter_num is not None:  # Ensure shooter_num is an int
            if self.shooter_num not in self.shooter_stats:
                self.shooter_stats[self.shooter_num] = {
                    "points_rolled": 0,
                    "rolls_before_7_out": [],
                    "shooter_rolls": 0,
                }
            self.shooter_stats[self.shooter_num]["points_rolled"] += 1

    def update_shooter_stats(self, shooter: Any) -> None:
        """Update shooter statistics."""
        if self.shooter_num is None:
            return  # Avoid indexing with None

        if self.shooter_num not in self.shooter_stats:
            self.shooter_stats[self.shooter_num] = {
                "points_rolled": 0,
                "rolls_before_7_out": [],
                "shooter_rolls": 0,
            }
        self.shooter_stats[self.shooter_num]["shooter_rolls"] = shooter.current_roll_count
        self.shooter_stats[self.shooter_num]["rolls_before_7_out"].append(shooter.rolls_before_7_out)

    def print_shooter_report(self) -> None:
        """Print a report summarizing each shooter's performance."""
        logging.info("\n=== Shooter Performance Report ===")
        for shooter_num, stats in self.shooter_stats.items():
            total_points_rolled = stats["points_rolled"]
            shooter_rolls = stats["shooter_rolls"]
            rolls_before_7_out = stats["rolls_before_7_out"]
            avg_rolls_before_7_out = (
                sum(rolls_before_7_out) / len(rolls_before_7_out)
                if rolls_before_7_out else 0
            )

            logging.info(
                f"  Shooter #{shooter_num}: {shooter_rolls} rolls "
                f"({total_points_rolled} points made, "
                f"{len(rolls_before_7_out)} 7-outs, "
                f"avg rolls before 7-out: {avg_rolls_before_7_out:.2f})"
            )

    def average_rolls_per_shooter(self) -> float:
        """Average number of rolls per shooter."""
        if self.num_shooters == 0:
            return 0.0
        return self.session_rolls / self.num_shooters

    def estimated_session_time_minutes(self, rolls_per_hour: int = 90) -> int:
        """Estimate session duration in minutes."""
        if rolls_per_hour <= 0:
            return 0
        return int((self.session_rolls / rolls_per_hour) * 60)

    def house_take(self) -> int:
        """Total house profit."""
        return self.total_amount_lost - self.total_amount_won

    def house_edge(self) -> float:
        """Effective house edge as a percentage of total amount bet."""
        if self.total_amount_bet == 0:
            return 0.0
        return (self.house_take() / self.total_amount_bet) * 100

    def get_estimated_session_time(self) -> str:
        total_minutes = round((self.session_rolls / 90) * 60)
        rounded_minutes = int(round(total_minutes / 15.0) * 15)
        hours = rounded_minutes // 60
        minutes = rounded_minutes % 60
        if hours and minutes:
            return f"{hours} hr {minutes} min"
        elif hours:
            return f"{hours} hr"
        else:
            return f"{minutes} min"

    def record_table_risk(self, table_risk: int) -> None:
        self.max_table_risk = max(self.max_table_risk, table_risk)

    def record_roll_total(self, total: int) -> None:
        if total == 7:
            self.total_sevens += 1

    def seven_roll_ratio(self) -> float:
        if self.session_rolls == 0:
            return 0.0
        return self.total_sevens / self.session_rolls
