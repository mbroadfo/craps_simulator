# File: main.py
from colorama import init, Fore, Style
init()  # Initialize colorama for colored text

from config import ACTIVE_PLAYERS, SESSION_MODE
from craps.house_rules import HouseRules
from craps.table import Table
from craps.lineup import PlayerLineup
from craps.single_session import run_single_session
from craps.roll_history_manager import RollHistoryManager  # Import the new class

def main():
    # Initialize the RollHistoryManager
    roll_history_manager = RollHistoryManager()

    # Prepare for the session based on the session mode
    try:
        roll_history_manager.prepare_for_session(SESSION_MODE)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
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
    stats = run_single_session(
        house_rules,
        strategies,
        player_names=player_names,
        roll_history_file=roll_history_manager.roll_history_file if SESSION_MODE == "history" else None
    )

    # Save the roll history if running in live mode
    if SESSION_MODE == "live":
        roll_history_manager.save_roll_history(stats.roll_history)

    # Print statistics
    stats.print_statistics()
    stats.print_shooter_report()

if __name__ == "__main__":
    main()