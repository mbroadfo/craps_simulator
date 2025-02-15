# File: craps/single_session.py
from colorama import init, Fore, Style
from craps.table import Table
from craps.game_state import GameState
from craps.shooter import Shooter
from craps.statistics import Statistics

def run_single_session(house_rules, strategies, player_names=None, initial_bankroll=500, num_shooters=10):
    """
    Run a single session of craps.
    
    :param house_rules: The HouseRules object for payout rules and limits.
    :param strategies: A list of betting strategies to evaluate.
    :param player_names: A list of names for the players (optional).
    :param initial_bankroll: The initial bankroll for each player.
    :param num_shooters: The number of shooters per session.
    :return: The Statistics object containing session results.
    """
    # Initialize components
    table = Table(house_rules)
    stats = Statistics(house_rules.table_minimum, num_shooters, len(strategies))
    game_state = GameState(stats, players=[])

    # Create players with different betting strategies
    if player_names is None:
        player_names = [f"Player {i+1}" for i in range(len(strategies))]

    players = [
        Shooter(player_names[i], initial_balance=initial_bankroll, betting_strategy=strategy)
        for i, strategy in enumerate(strategies)
    ]
    game_state.players = players

    # Initialize bankroll history with the starting bankroll for each player
    stats.initialize_bankroll_history(players)

    # Simulate shooters
    for shooter_num in range(1, num_shooters + 1):
        player_index = (shooter_num - 1) % len(players)
        shooter = players[player_index]
        game_state.set_shooter(shooter)

        while True:
            # Allow all players to place bets
            for player in players:
                bet = player.betting_strategy.get_bet(game_state, player)
                if bet:
                    player.place_bet(bet, table)

            # Roll the dice and resolve bets
            outcome = shooter.roll_dice()
            total = sum(outcome)
            stats.update_rolls()

            # Print the dice roll and total
            print(f"{Fore.LIGHTMAGENTA_EX}{shooter.name} rolled: {outcome} (Total: {total}) | Roll Count: {stats.num_rolls}{Style.RESET_ALL}")

            # Check bets on the table
            table.check_bets(outcome, game_state.phase, game_state.point)

            # Resolve bets for each player and update their bankroll
            for player in players:
                player.resolve_bets(table, stats, outcome, game_state.phase, game_state.point)

            # Update player bankrolls in statistics
            stats.update_player_bankrolls(players)
            
            # Update game state
            previous_phase = game_state.phase
            message = game_state.update_state(outcome)
            if message:
                print(message)

            # Check if the shooter 7-outs
            if previous_phase == "point" and total == 7:
                stats.record_seven_out()
                break

    return stats