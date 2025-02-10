# File: .\main.py

from colorama import init
init()  # Initialize colorama for colored text

from craps.table import Table
from craps.game_state import GameState
from craps.shooter import Shooter
from craps.strategies.pass_line import PassLineStrategy
from craps.strategies.place_bet import PlaceBetStrategy
from craps.statistics import Statistics

def main():
    # Initialize components
    table_minimum = 10  # Set table minimum
    table = Table(table_minimum=table_minimum)
    game_state = GameState()

    # Set the number of players, shooters, and initial bankroll
    num_players = 3
    num_shooters = 10
    initial_bankroll = 500

    # Initialize statistics
    stats = Statistics(table_minimum, num_shooters, num_players)

    # Create players with different betting strategies
    players = [
        Shooter(f"Player {i+1}", initial_balance=initial_bankroll, betting_strategy=PassLineStrategy(min_bet=10))
        if i == 0 else
        Shooter(f"Player {i+1}", initial_balance=initial_bankroll, betting_strategy=PlaceBetStrategy(table, "inside"))
        if i == 1 else
        Shooter(f"Player {i+1}", initial_balance=initial_bankroll, betting_strategy=PlaceBetStrategy(table, "across"))
        for i in range(num_players)
    ]

    # Simulate shooters
    for shooter_num in range(1, num_shooters + 1):
        player_index = (shooter_num - 1) % num_players
        shooter = players[player_index]
        game_state.set_shooter(shooter)
        print(f"\nShooter {shooter_num} is {shooter.name}. It's their turn to roll.")

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
            print(f"{shooter.name} rolled: {outcome} (Total: {total}) | Roll Count: {stats.num_rolls}")

            # Check bets on the table
            table.check_bets(outcome, game_state)

            # Resolve bets for each player and update their bankroll
            for player in players:
                player.resolve_bets(table, stats)  # Pass stats to resolve_bets
            
            # Update game state
            previous_phase = game_state.phase
            message = game_state.update_state(outcome)
            if message:
                print(message)

            # Check if the shooter 7-outs (only if the point was set)
            if previous_phase == "point" and total == 7:
                print(f"{shooter.name} has 7-ed out. Their turn is over.")
                break

    # Update player bankrolls and calculate statistics
    stats.update_player_bankrolls(players)
    stats.print_statistics()

if __name__ == "__main__":
    main()