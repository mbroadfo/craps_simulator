# File: main.py
from colorama import init, Fore, Style
init()  # Initialize colorama for colored text

import os
from config import ACTIVE_PLAYERS, SESSION_MODE  # Import the new SESSION_MODE
from craps.house_rules import HouseRules
from craps.table import Table
from craps.lineup import PlayerLineup
from craps.single_session import run_single_session

def main():
    # Define the output folder and roll history file
    output_folder = 'output'
    roll_history_file = os.path.join(output_folder, 'single_session_roll_history.csv')

    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Handle live and history modes
    if SESSION_MODE == "live":
        # Delete the roll history file if it exists
        if os.path.exists(roll_history_file):
            os.remove(roll_history_file)
            print(f"Deleted existing roll history file: {roll_history_file}")
        
        # Run a live session and save the roll history to a CSV file
        print("Running session in 'live' mode with random rolls.")
    elif SESSION_MODE == "history":
        # Check if the roll history file exists
        if not os.path.exists(roll_history_file):
            print(f"Error: Roll history file '{roll_history_file}' not found. Please run in 'live' mode first.")
            return
        # Replay a session using the roll history file
        print(f"Running session in 'history' mode using roll history from: {roll_history_file}")
    else:
        print(f"Error: Invalid SESSION_MODE '{SESSION_MODE}'. Must be 'live' or 'history'.")
        return

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

    # Run the session
    stats = run_single_session(house_rules, strategies, player_names=player_names, roll_history_file=roll_history_file)

    # Print statistics
    stats.print_statistics()
    stats.print_shooter_report()

if __name__ == "__main__":
    main()