from colorama import init, Fore, Style
from typing import List, Optional, Any
from craps.table import Table
from craps.game_state import GameState
from craps.shooter import Shooter
from craps.dice import Dice
from craps.statistics import Statistics
from craps.rules_engine import RulesEngine
from craps.play_by_play import PlayByPlay
from craps.house_rules import HouseRules
import os

def run_single_session(
    house_rules: HouseRules,
    strategies: List[Any],
    player_names: Optional[List[str]] = None, 
    initial_bankroll: int = 500, 
    num_shooters: int = 10, 
    roll_history_file: Optional[str] = None, 
    play_by_play: PlayByPlay = PlayByPlay()
) -> Statistics:
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
    rules_engine = RulesEngine()
    table = Table(house_rules, play_by_play, rules_engine)
    stats = Statistics(house_rules.table_minimum, num_shooters, len(strategies))
    stats.roll_history = []  # Ensure roll_history is initialized
    game_state = GameState(stats, play_by_play=play_by_play)
    game_state.set_table(table)

    # Create players with different betting strategies
    if player_names is None:
        player_names = [f"Player {i+1}" for i in range(len(strategies))]

    players = [
        Shooter(player_names[i], initial_balance=initial_bankroll, betting_strategy=strategy, dice=dice, play_by_play=play_by_play)
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
        stats.set_shooter(shooter, shooter_num)

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
            stats.update_shooter_stats(shooter)

            # Log the dice roll and total
            message = f"{Fore.LIGHTMAGENTA_EX}{shooter.name} rolled: {outcome} (Total: {total}) | Roll Count: {stats.num_rolls}{Style.RESET_ALL}"
            play_by_play.write(message)  # Write the message to the play-by-play file

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
                    message = f"{Fore.RED}❌ {bet.owner.name}'s {bet.bet_type} bet LOST ${bet.amount}.{Style.RESET_ALL}"
                    play_by_play.write(message)  # Write the message to the play-by-play file
                stats.update_win_loss(bet)

            # Update player bankrolls in statistics
            stats.update_player_bankrolls(players)

            # Update game state
            previous_phase = game_state.phase
            message = game_state.update_state(outcome)
            if message:
                play_by_play.write(message)  # Write the message to the play-by-play file

            # Check if the shooter 7-outs
            if previous_phase == "point" and total == 7:
                stats.record_seven_out()
                shooter_num += 1  # Rotate to next shooter immediately
                break

    # Return stats and roll history
    stats.roll_history = roll_history
    return stats