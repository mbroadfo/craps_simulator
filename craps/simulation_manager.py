# File: craps/simulation_manager.py
from typing import List
from craps.single_session import run_single_session
from craps.house_rules import HouseRules
from craps.statistics import Statistics
from craps.view_log import InteractiveLogViewer
class SimulationManager:
    def __init__(self, house_rules: HouseRules, num_tables: int, num_shooters: int, strategies: List):
        """
        Initialize the SimulationManager.
        
        :param house_rules: The HouseRules object for payout rules and limits.
        :param num_tables: The number of tables to simulate.
        :param num_shooters: The number of shooters per session.
        :param strategies: A list of betting strategies to evaluate.
        """
        self.house_rules = house_rules
        self.num_tables = num_tables
        self.num_shooters = num_shooters
        self.strategies = strategies
        self.stats = Statistics(house_rules.table_minimum, num_shooters, len(strategies))

    def run_simulation(self, num_sessions: int) -> None:
        """Run multiple sessions and collect statistics."""
        for _ in range(num_sessions):
            for _ in range(self.num_tables):
                stats = run_single_session(self.house_rules, self.strategies, num_shooters=self.num_shooters)
                self.stats.merge(stats)  # Merge session stats into overall stats

        # View the statistics report
        log_viewer = InteractiveLogViewer()
        log_viewer.view("output/statistics_report.txt")
        self.stats.print_shooter_report()
