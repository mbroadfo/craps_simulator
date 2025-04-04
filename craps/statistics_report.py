import os
from craps.statistics import Statistics

class StatisticsReport:
    def __init__(self, filepath: str = "output/statistics_report.txt") -> None:
        self.filepath = filepath
        self.clear_statistics_file()

    def clear_statistics_file(self) -> None:
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def write(self, line: str) -> None:
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def write_statistics(self, stats: "Statistics") -> None:
        self.write(f"=============================================")
        self.write("📊 Simulation Statistics")
        self.write(f"📌 Table Minimum: ${stats.table_minimum}")
        self.write(f"👥 Number of Players: {stats.num_players}")
        self.write(f"🎯 Number of Shooters: {stats.num_shooters}")
        self.write(f"🎲 Session Rolls: {stats.session_rolls}")
        self.write(f"🧮 Rolls per Shooter: {stats.session_rolls / stats.num_shooters:.2f}")
        self.write(f"⏱️ Estimated Session Time: {stats.get_estimated_session_time()}")
        self.write(f"💸 Total Amount Bet: ${stats.total_amount_bet}")
        self.write(f"💰 Total Amount Won: ${stats.total_amount_won}")
        self.write(f"❌ Total Amount Lost: ${stats.total_amount_lost}")
        self.write(f"🏦 House Take: ${stats.total_amount_lost - stats.total_amount_won}")
        house_edge = ((stats.total_amount_lost - stats.total_amount_won) / stats.total_amount_bet * 100
                    if stats.total_amount_bet else 0.0)
        self.write(f"🎲 House Edge: {house_edge:.2f}%")
        self.write(f"🔺 Highest Bankroll During Session: ${stats.session_highest_bankroll}")
        self.write(f"🔻 Lowest Bankroll During Session: ${stats.session_lowest_bankroll}")
