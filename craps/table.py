# File: .\craps\table.py

class Table:
    def __init__(self, table_minimum=5):
        """
        Initialize the table with a minimum bet.
        
        :param table_minimum: The minimum bet for the table (e.g., 5, 10, 15, 25).
        """
        self.bets = []
        self.table_minimum = table_minimum
        self.unit = table_minimum // 5  # Unit is table minimum divided by 5

    def place_bet(self, bet):
        """Place a bet on the table."""
        self.bets.append(bet)

    def check_bets(self, outcome, game_state):
        """Resolve all bets on the table based on the dice outcome and game state."""
        total = sum(outcome)
        
        for bet in self.bets:
            # Resolve Pass Line and Pass Line Odds bets
            if bet.bet_type in ["Pass Line", "Pass Line Odds"]:
                bet.resolve(outcome, game_state)
            
            # Resolve Place bets only during the point phase
            elif bet.bet_type.startswith("Place"):
                if game_state.phase == "point":
                    if total == bet.number or total == 7:
                        bet.resolve(outcome, game_state)
            
            # Add logic for other bet types if needed

        # Remove all resolved bets (won or lost), but keep active and inactive bets
        self.bets = [bet for bet in self.bets if bet.status in ["active", "inactive"]]

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