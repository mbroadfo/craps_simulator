# File: main.py
from colorama import init, Fore, Style
init()  # Initialize colorama for colored text

from craps.house_rules import HouseRules
from craps.single_session import run_single_session
from craps.visualizer import Visualizer
from craps.table import Table
from craps.view_log import InteractiveLogViewer
from lineup import PlayerLineup  # Import the PlayerLineup class
from config import ACTIVE_PLAYERS   # Import the list of active players
import logging

# Configure logging
logging.basicConfig(
    filename='play_by_play.log',
    level=logging.INFO,
    format='%(message)s',  # No timestamp, just the message
    encoding='utf-8'  # Ensure UTF-8 encoding
)

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

    # View the log file interactively
    log_viewer = InteractiveLogViewer()
    log_viewer.view('./play_by_play.log')
    
    # Visualize player bankrolls
    visualizer = Visualizer(stats)
    visualizer.visualize_bankrolls()
    
if __name__ == "__main__":
    main()