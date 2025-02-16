import json
import os
from craps.table import Table
from craps.house_rules import HouseRules
from craps.game_state import GameState
from craps.statistics import Statistics
from lineup import PlayerLineup
from ..config import ACTIVE_PLAYERS

def replay_single_session(roll_history_file=os.path.join('output', 'single_session_roll_history.json')):
    """
    Replay a single craps session using the roll history.
    """
    # Load the roll history
    with open(roll_history_file, 'r', encoding='utf-8') as f:
        roll_history = json.load(f)

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

    # Initialize game state and statistics
    stats = Statistics(house_rules.table_minimum, len(roll_history), len(strategies))
    game_state = GameState(stats, players=[])

    # Create players with different betting strategies
    players = [
        Shooter(player_names[i], initial_balance=500, betting_strategy=strategy)
        for i, strategy in enumerate(strategies)
    ]
    game_state.players = players

    # Initialize bankroll history with the starting bankroll for each player
    stats.initialize_bankroll_history(players)

    # Replay each roll
    for roll in roll_history:
        # Update game state
        game_state.phase = roll["phase"]
        game_state.point = roll["point"]

        # Simulate the dice roll
        outcome = roll["dice"]
        total = roll["total"]

        # Print the dice roll and total
        print(f"Roll {roll['roll_number']}: {outcome} (Total: {total}) | Phase: {game_state.phase} | Point: {game_state.point}")

        # Check bets on the table
        table.check_bets(outcome, game_state.phase, game_state.point)

        # Resolve bets for each player and update their bankroll
        for player in players:
            player.resolve_bets(table, stats, outcome, game_state.phase, game_state.point)

        # Update player bankrolls in statistics
        stats.update_player_bankrolls(players)

    # Print statistics
    stats.print_statistics()
    stats.print_shooter_report()

if __name__ == "__main__":
    replay_single_session()