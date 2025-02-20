# File: .\main.py

from colorama import init, Fore, Style
from config import ACTIVE_PLAYERS, SESSION_MODE, HOUSE_RULES
from craps.session_initializer import InitializeSession
from craps.player_setup import SetupPlayers
from craps.single_session import run_single_session
from craps.visualizer import Visualizer
from craps.view_log import InteractiveLogViewer

def main():
    init()  # Initialize colorama for colored text

    # Initialize the session
    session_initializer = InitializeSession(SESSION_MODE, HOUSE_RULES)
    result = session_initializer.prepare_session()
    if not result:
        return  # Exit if session initialization fails

    house_rules, table, roll_history_manager, log_manager = result

    # Set up players
    player_setup = SetupPlayers(house_rules, table, ACTIVE_PLAYERS)
    strategies, player_names = player_setup.setup()

    # Get the roll history file based on the session mode
    roll_history_file = roll_history_manager.get_roll_history_file(SESSION_MODE)

    # Run the session
    stats = run_single_session(house_rules, strategies, player_names=player_names, roll_history_file=roll_history_file)

    # Save the roll history if running in live mode
    if SESSION_MODE == "live":
        roll_history_manager.save_roll_history(stats.roll_history)

    # Print statistics
    stats.print_statistics()
    stats.print_shooter_report()
    
    # View the log file interactively
    log_viewer = InteractiveLogViewer()
    log_viewer.view(log_manager.log_file)  # Use the correct log file path
    
    # Visualize player bankrolls
    visualizer = Visualizer(stats)
    visualizer.visualize_bankrolls()
    
    # Close the log file properly
    log_manager.close_log_file()

if __name__ == "__main__":
    main()