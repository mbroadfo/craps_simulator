from colorama import init, Fore, Style
from typing import List, Optional, Any
from craps.table import Table
from craps.game_state import GameState
from craps.player import Player
from craps.dice import Dice
from craps.statistics import Statistics
from craps.house_rules import HouseRules
from craps.log_manager import LogManager
from craps.session_initializer import InitializeSession
import os

def run_single_session(
    house_rules: HouseRules,
    strategies: List[Any],
    player_names: Optional[List[str]] = None, 
    initial_bankroll: int = 500, 
    num_shooters: int = 10, 
    roll_history_file: Optional[str] = None
) -> Statistics:
    """
    Run a single session of craps and log the roll history.
    """
    init()  # Initialize colorama

    # Set dice mode
    dice = Dice(roll_history_file) if roll_history_file and os.path.exists(roll_history_file) else Dice()

    # Initialize session
    session_initializer = InitializeSession(
        session_mode="live", 
        house_rules_config={"table_minimum": house_rules.table_minimum, "table_maximum": house_rules.table_maximum}
    )
    session_data = session_initializer.prepare_session(num_shooters, len(strategies))
    
    if session_data is None:
        raise RuntimeError("Failed to initialize session.")

    house_rules, table, roll_history_manager, log_manager, play_by_play, stats, game_state = session_data

    # Create players with different betting strategies
    if player_names is None:
        player_names = [f"Player {i+1}" for i in range(len(strategies))]

    players = [
        Player(player_names[i], initial_balance=initial_bankroll, betting_strategy=strategy)
        for i, strategy in enumerate(strategies)
    ]

    # Initialize bankroll history with the starting bankroll for each player
    stats.initialize_bankroll_history(players)

    # Initialize roll history
    roll_history = []

    # Simulate shooters
    for shooter_num in range(1, num_shooters + 1):
        player_index = (shooter_num - 1) % len(players)
        shooter = players[player_index]

        # Assign new shooter via GameState
        game_state.assign_new_shooter(shooter)

        while True:
            # Allow all players to place bets
            for player in players:
                bet = player.betting_strategy.get_bet(game_state, player, table)
                if bet:
                    player.place_bet(bet, table, game_state.phase, play_by_play)

            # Roll the dice and resolve bets
            outcome = (dice.roll())  # Now returns Tuple[int, int]
            total = sum(outcome)
            stats.update_rolls()
            stats.update_shooter_stats(shooter)

            # Log the dice roll and total
            message = f"{Fore.LIGHTMAGENTA_EX}{shooter.name} rolled: {outcome} (Total: {total}) | Roll Count: {stats.num_rolls}{Style.RESET_ALL}"
            play_by_play.write(message)

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
                    bet.owner.receive_payout(payout, play_by_play)
                elif bet.status == "lost":
                    message = f"{Fore.RED}❌ {bet.owner.name}'s {bet.bet_type} bet LOST ${bet.amount}.{Style.RESET_ALL}"
                    play_by_play.write(message)
                stats.update_win_loss(bet)

            # Update player bankrolls in statistics
            stats.update_player_bankrolls(players)

            # Update game state
            previous_phase = game_state.phase
            message = game_state.update_state(outcome)
            if message:
                play_by_play.write(message)

            # Check if the shooter 7-outs
            if previous_phase == "point" and total == 7:
                stats.record_seven_out()
                game_state.clear_shooter()  # Reset shooter status
                break  # Move to next shooter

    # Return stats and roll history
    stats.roll_history = roll_history
    return stats
