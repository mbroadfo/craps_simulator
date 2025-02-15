# File: main.py
from colorama import init, Fore, Style
init()  # Initialize colorama for colored text

from craps.house_rules import HouseRules
from craps.single_session import run_single_session
from craps.strategies.pass_line import PassLineStrategy
from craps.strategies.pass_line_odds import PassLineOddsStrategy
from craps.strategies.place_bet import PlaceBetStrategy
from craps.strategies.field_bet import FieldBetStrategy
from craps.visualizer import Visualizer
from craps.table import Table  # Import the Table class

def main():
    # Initialize house rules
    house_rules = HouseRules()
    house_rules.set_field_bet_payouts((3, 1), (2, 1))  # 3:1 for 2, 2:1 for 12
    house_rules.set_table_limits(10, 1000)  # Table limits

    # Create the Table object
    table = Table(house_rules)

    # Define strategies to evaluate
    strategies = [
        PassLineStrategy(min_bet=house_rules.table_minimum),  # Pass-Line
        PassLineOddsStrategy(table=table, odds_multiple=1),  # Pass-Line w/ Odds
        PlaceBetStrategy(table=table, numbers_or_strategy="inside"),  # $44 Inside
        PlaceBetStrategy(table=table, numbers_or_strategy="across"),  # $54 Across
        FieldBetStrategy(min_bet=house_rules.table_minimum)  # Field
    ]

    # Define player names
    player_names = [
        "Pass-Line",
        "Pass-Line w/ Odds",
        "$44 Inside",
        "$54 Across",
        "Field"
    ]

    # Run a single session
    stats = run_single_session(house_rules, strategies, player_names=player_names)

    # Print statistics
    stats.print_statistics()
    stats.print_shooter_report()

    # Visualize player bankrolls
    visualizer = Visualizer(stats)
    visualizer.visualize_bankrolls()

if __name__ == "__main__":
    main()