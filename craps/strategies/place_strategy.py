# File: .\craps\strategies\place_strategy.py

from craps.rules_engine import RulesEngine  # Import RulesEngine

class PlaceBetStrategy:
    """Betting strategy for Place Bets."""
    def __init__(self, table, numbers_or_strategy):
        """
        Initialize the Place Bet strategy.
        
        :param table: The table object to determine minimum bets.
        :param numbers_or_strategy: A list of numbers (e.g., [5, 6, 8, 9]) or a strategy ("inside", "across").
        """
        self.table = table
        self.numbers_or_strategy = numbers_or_strategy
        self.rules_engine = RulesEngine()  # Initialize RulesEngine

    def get_bet(self, game_state, player, table):
        """Place Place Bets based on the strategy and game state."""
        if game_state.phase != "point":
            return None  # Only place bets after the point is established

        # Determine which numbers to bet on
        if isinstance(self.numbers_or_strategy, str):
            if self.numbers_or_strategy == "inside":
                numbers = [5, 6, 8, 9]  # Inside numbers
            elif self.numbers_or_strategy == "across":
                numbers = [4, 5, 6, 8, 9, 10]  # Across numbers
            else:
                raise ValueError(f"Invalid strategy: {self.numbers_or_strategy}")
        else:
            numbers = self.numbers_or_strategy  # Specific numbers provided

        # Filter out numbers already covered by a Pass Line bet or a Place bet
        numbers = [
            num for num in numbers
            if not any(
                (bet.owner == player and bet.bet_type == "Pass Line" and bet.point == num) or  # Pass Line covers the point
                (bet.owner == player and bet.bet_type.startswith("Place") and bet.number == num)  # Place Bet covers the number
                for bet in table.bets
            )
        ]

        # Use RulesEngine to create Place bets
        bets = []
        for number in numbers:
            min_bet = self.table.get_minimum_bet(number)
            bets.append(self.rules_engine.create_bet("Place", min_bet, player, number=number))

        return bets if bets else None