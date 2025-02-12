# File: .\craps\table.py

class Table:
    def __init__(self, table_minimum=5, game_state=None):
        """
        Initialize the table with a minimum bet.
        
        :param table_minimum: The minimum bet for the table (e.g., 5, 10, 15, 25).
        :param game_state: The GameState object to track the game state.
        """
        self.bets = []
        self.table_minimum = table_minimum
        self.unit = table_minimum // 5  # Unit is table minimum divided by 5
        self.game_state = game_state  # Store the game state

    def place_bet(self, bet):
        """Place a bet on the table."""
        self.bets.append(bet)

    def check_bets(self, outcome, game_state):
        """Check and resolve all bets on the table based on the dice outcome and game state."""
        total = sum(outcome)

        # Create a copy of bets to avoid modifying the list while iterating
        bets_copy = self.bets.copy()

        for bet in bets_copy:
            # Only resolve active bets
            if bet.status == "active":
                bet.resolve(outcome, game_state)

        # If a 7-out occurs, clear all bets from the table
        if game_state.phase == "come-out" and total == 7:
            self.bets.clear()

    def get_minimum_bet(self, number):
        """
        Get the minimum bet for a Place bet on a specific number.
        
        :param number: The number being bet on (4, 5, 6, 8, 9, or 10).
        :return: The minimum bet amount.
        """
        if number in [6, 8]:
            # For 6 and 8, the minimum bet is table minimum + unit
            return self.table_minimum + self.unit
        else:
            # For other numbers, the minimum bet is the table minimum
            return self.table_minimum