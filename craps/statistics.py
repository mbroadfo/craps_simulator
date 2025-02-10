# File: .\craps\statistics.py

class Statistics:
    """Class to track and calculate simulation statistics."""
    def __init__(self, table_minimum, num_shooters, num_players):
        """
        Initialize the statistics tracker.
        
        :param table_minimum: The minimum bet for the table.
        :param num_shooters: The number of shooters in the simulation.
        :param num_players: The number of players in the simulation.
        """
        self.table_minimum = table_minimum
        self.num_shooters = num_shooters
        self.num_players = num_players
        self.num_rolls = 0
        self.total_house_win_loss = 0
        self.total_player_win_loss = 0
        self.player_bankrolls = []
        self.highest_bankroll = 0
        self.lowest_bankroll = float('inf')

    def update_rolls(self):
        """Increment the roll count."""
        self.num_rolls += 1

    def update_house_win_loss(self, amount):
        """Update the total house win/loss."""
        self.total_house_win_loss += amount

    def update_player_win_loss(self, amount):
        """Update the total player win/loss."""
        self.total_player_win_loss += amount

    def update_player_bankrolls(self, players):
        """Update player bankrolls and track highest/lowest bankroll."""
        self.player_bankrolls = [player.balance for player in players]
        self.highest_bankroll = max(self.player_bankrolls)
        self.lowest_bankroll = min(self.player_bankrolls)

    def print_statistics(self):
        """Print the simulation statistics."""
        print("\n=== Simulation Statistics ===")
        print(f"Table Minimum: ${self.table_minimum}")
        print(f"Number of Shooters: {self.num_shooters}")
        print(f"Number of Players: {self.num_players}")
        print(f"Number of Rolls: {self.num_rolls}")
        print(f"Total House Win/Loss: ${self.total_house_win_loss}")
        print(f"Total Player Win/Loss: ${self.total_player_win_loss}")
        print(f"Player Bankrolls: {self.player_bankrolls}")
        print(f"Highest Player Bankroll: ${self.highest_bankroll}")
        print(f"Lowest Player Bankroll: ${self.lowest_bankroll}")