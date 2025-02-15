# File: main.py
from colorama import init, Fore, Style
init()  # Initialize colorama for colored text

from craps.house_rules import HouseRules
from craps.single_session import run_single_session
from craps.visualizer import Visualizer
from craps.table import Table
from lineup import PlayerLineup  # Import the PlayerLineup class

# Import the configuration
from config import ACTIVE_PLAYERS

def main():
    # Initialize house rules
    house_rules = HouseRules()
    house_rules.set_field_bet_payouts((3, 1), (2, 1))  # 3:1 for 2, 2:1 for 12
    house_rules.set_table_limits(10, 1000)  # Table limits

    # Create the Table object
    table = Table(house_rules)

    # Initialize the player lineup
    player_lineup = PlayerLineup(house_rules, table)

    # Get active strategies and player names
    strategies, player_names = player_lineup.get_active_players(ACTIVE_PLAYERS)

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