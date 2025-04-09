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
        self.write_player_statistics(stats)
        self.write_session_statistics(stats)
    
    def write_player_statistics(self, stats: "Statistics") -> None:
        self.write("\n=============================================")
        self.write("🧑‍🤝‍🧑 Player Performance Report\n")

        for name, data in stats.player_stats.items():
            net = data["net_win_loss"]
            result = "Won" if net >= 0 else "Lost"
            sign = "+" if net >= 0 else "-"
            max_at_risk = max(stats.at_risk_history.get(name, [0]))

            # Derived stat
            settled = data["bets_settled"]
            won = data["bets_won"]
            win_rate = (won / settled * 100) if settled > 0 else 0.0

            self.write(f"🎲 {name}")
            self.write(f"  📥 Initial Bankroll: ${data['initial_bankroll']}")
            self.write(f"  📤 Final Bankroll:   ${data['final_bankroll']}")
            self.write(f"  📊 Net Result:       {sign}${abs(net)} ({result})")
            self.write(f"  🎯 Bets Settled:     {settled}")
            self.write(f"  ✅ Bets Won:         {won} ({win_rate:.1f}% win rate)")
            self.write(f"  🔥 Max At-Risk:      ${max_at_risk}")
            self.write(f"  🔺 Highest Bankroll: ${data['highest_bankroll']}")
            self.write(f"  🔻 Lowest Bankroll:  ${data['lowest_bankroll']}\n")

    def write_session_statistics(self, stats: "Statistics") -> None:
        self.write(f"=============================================")
        self.write("📊 Simulation Statistics")
        self.write(f"📌 Table Minimum: ${stats.table_minimum}")
        self.write(f"👥 Number of Players: {stats.num_players}")
        self.write(f"🎯 Number of Shooters: {stats.num_shooters}")
        self.write(f"⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋")
        self.write(f"🎲 Session Rolls: {stats.session_rolls}")
        self.write(f"🧮 Rolls per Shooter: {stats.session_rolls / stats.num_shooters:.2f}")
        self.write(f"⏱️ Estimated Session Time: {stats.get_estimated_session_time()}")
        self.write(f"📉 Max Table Risk: ${stats.max_table_risk}")
        self.write(f"💸 Total Amount Bet: ${stats.total_amount_bet}")
        self.write(f"💰 Total Amount Won: ${stats.total_amount_won}")
        self.write(f"❌ Total Amount Lost: ${stats.total_amount_lost}")
        self.write(f"🏦 House Take: ${stats.total_amount_lost - stats.total_amount_won}")
        house_edge = ((stats.total_amount_lost - stats.total_amount_won) / stats.total_amount_bet * 100
                    if stats.total_amount_bet else 0.0)
        self.write(f"🎲 House Edge: {house_edge:.2f}%")
        self.write(f"😈 Total 7s Rolled: {stats.total_sevens}")
        self.write(f"🎯 7-Roll Ratio (SRR): {stats.seven_roll_ratio():.2f}")
        self.write(f"🔺 Highest Bankroll During Session: ${stats.session_highest_bankroll}")
        self.write(f"🔻 Lowest Bankroll During Session: ${stats.session_lowest_bankroll}")
