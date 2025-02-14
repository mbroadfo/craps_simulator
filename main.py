# File: main.py
from colorama import init, Fore, Style
init()  # Initialize colorama for colored text

from craps.table import Table
from craps.game_state import GameState
from craps.shooter import Shooter
from craps.strategies.pass_line import PassLineStrategy
from craps.strategies.pass_line_odds import PassLineOddsStrategy
from craps.strategies.place_bet import PlaceBetStrategy
from craps.statistics import Statistics
from craps.visualizer import Visualizer

def main():
    # Initialize components
    table_minimum = 10  # Set table minimum
    stats = Statistics(table_minimum, num_shooters=10, num_players=3)  # Initialize stats

    # Create the GameState object
    game_state = GameState(stats, players=[])  # Pass stats and empty players list initially

    # Create the Table object
    table = Table(table_minimum=table_minimum)

    # Set the number of players, shooters, and initial bankroll
    num_shooters = 10
    initial_bankroll = 500

    # Create players with different betting strategies
    players = [
        Shooter("Pass Line", initial_balance=initial_bankroll, betting_strategy=PassLineStrategy(min_bet=table_minimum)),
        Shooter("2x Odds", initial_balance=initial_bankroll, betting_strategy=PassLineOddsStrategy(table, 2)),
        Shooter("44 Inside", initial_balance=initial_bankroll, betting_strategy=PlaceBetStrategy(table, "across"))
    ]
    num_players = len(players)
    
    # Update the GameState with the players
    game_state.players = players

    # Simulate shooters
    for shooter_num in range(1, num_shooters + 1):
        player_index = (shooter_num - 1) % num_players
        shooter = players[player_index]
        game_state.set_shooter(shooter)
        print(f"\n{Fore.CYAN}Shooter {shooter_num} is {shooter.name}. It's their turn to roll.{Style.RESET_ALL}")

        while True:
            # Allow all players to place bets
            for player in players:
                bet = player.betting_strategy.get_bet(game_state, player)
                if bet:
                    player.place_bet(bet, table)

            # Roll the dice and resolve bets
            outcome = shooter.roll_dice()
            total = sum(outcome)
            stats.update_rolls()  # Update roll count
            print(f"{Fore.LIGHTMAGENTA_EX}{shooter.name} rolled: {outcome} (Total: {total}) | Roll Count: {stats.num_rolls}{Style.RESET_ALL}")

            # Check bets on the table
            table.check_bets(outcome, game_state.phase, game_state.point)

            # Resolve bets for each player and update their bankroll
            for player in players:
                player.resolve_bets(table, stats, outcome, game_state.phase, game_state.point)  # Pass phase and point

            # Update player bankrolls in statistics
            stats.update_player_bankrolls(players)

            # Update game state
            previous_phase = game_state.phase
            message = game_state.update_state(outcome)
            if message:
                print(message)

            # Reactivate inactive Place bets after resolving bets
            if game_state.phase == "point":
                for player in players:
                    for bet in player.active_bets:
                        if bet.bet_type.startswith("Place") and bet.status == "inactive":
                            bet.status = "active"
                            print(f"{player.name}'s {bet.bet_type} bet is now ACTIVE.")

            # Check if the shooter 7-outs (only if the point was set)
            if previous_phase == "point" and total == 7:
                print(f"{shooter.name} has 7-ed out. Their turn is over.")
                stats.record_seven_out()  # Record 7-out event

                # Resolve all bets for all players
                for player in players:
                    player.resolve_bets(table, stats, outcome, game_state.phase, game_state.point)  # Pass phase and point

                # Clear all bets from the table
                table.bets.clear()

                stats.update_shooter_stats(shooter)  # Update shooter statistics
                break

    # Update player bankrolls and calculate statistics
    stats.update_player_bankrolls(players)
    stats.print_statistics()
    stats.print_shooter_report()

    # Visualize player bankrolls
    visualizer = Visualizer(stats)
    visualizer.visualize_bankrolls()

if __name__ == "__main__":
    main()