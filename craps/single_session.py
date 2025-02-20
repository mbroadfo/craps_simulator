# File: .\craps\single_session.py

from colorama import init, Fore, Style
from craps.table import Table
from craps.game_state import GameState
from craps.shooter import Shooter
from craps.dice import Dice
from craps.statistics import Statistics
from craps.visualizer import Visualizer
import os
import logging

def run_single_session(house_rules, strategies, player_names=None, initial_bankroll=500, num_shooters=10, roll_history_file=None):
    """
    Run a single session of craps and log the roll history.
    """
    init()  # Initialize colorama

    # Set dice mode
    if roll_history_file and os.path.exists(roll_history_file):
        dice = Dice(roll_history_file)
    else:
        dice = Dice()  # Use random rolls

    # Initialize components
    table = Table(house_rules)
    stats = Statistics(house_rules.table_minimum, num_shooters, len(strategies))
    game_state = GameState(stats)  # Pass stats to GameState

    # Set the table in the game state
    game_state.set_table(table)

    # Create players with different betting strategies
    if player_names is None:
        player_names = [f"Player {i+1}" for i in range(len(strategies))]

    players = [
        Shooter(player_names[i], initial_balance=initial_bankroll, betting_strategy=strategy, dice=dice)
        for i, strategy in enumerate(strategies)
    ]
    game_state.set_players(players)

    # Initialize bankroll history with the starting bankroll for each player
    stats.initialize_bankroll_history(players)

    # Initialize roll history
    roll_history = []

    # Simulate shooters
    for shooter_num in range(1, num_shooters + 1):
        player_index = (shooter_num - 1) % len(players)
        shooter = players[player_index]
        game_state.set_shooter(shooter)

        while True:
            # Allow all players to place bets
            for player in players:
                bet = player.betting_strategy.get_bet(game_state, player, table)
                if bet:
                    player.place_bet(bet, table, game_state.phase)  # Pass the current phase

            # Roll the dice and resolve bets
            outcome = shooter.roll_dice()
            total = sum(outcome)
            stats.update_rolls()

            # Log the dice roll and total
            logging.info(f"{Fore.LIGHTMAGENTA_EX}{shooter.name} rolled: {outcome} (Total: {total}) | Roll Count: {stats.num_rolls}{Style.RESET_ALL}")

            # Log the roll to the history
            roll_history.append({
                "shooter_num": shooter_num,
                "roll_number": stats.num_rolls,
                "dice": outcome,
                "total": total,
                "phase": game_state.phase,
                "point": game_state.point
            })

            # Check bets on the table
            table.check_bets(outcome, game_state.phase, game_state.point)

            # Clear resolved bets and update player bankrolls
            resolved_bets = table.clear_resolved_bets()
            for bet in resolved_bets:
                if bet.status == "won":
                    payout = bet.payout()
                    bet.owner.receive_payout(payout)
                elif bet.status == "lost":
                    logging.info(f"{bet.owner.name}'s {bet.bet_type} bet LOST ${bet.amount}.")

            # Update player bankrolls in statistics
            stats.update_player_bankrolls(players)

            # Update game state
            previous_phase = game_state.phase
            message = game_state.update_state(outcome)
            if message:
                logging.info(message)

            # Check if the shooter 7-outs
            if previous_phase == "point" and total == 7:
                stats.record_seven_out()
                break

    # Return stats and roll history
    stats.roll_history = roll_history
    return stats