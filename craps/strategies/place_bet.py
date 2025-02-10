# File: .\craps\strategies\place_bet.py

from craps.bets.place_bet import PlaceBet

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

    def get_bet(self, game_state, player):
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
                (b.bet_type == "Pass Line" and b.point == num) or  # Pass Line covers the point
                (b.bet_type.startswith("Place") and b.number == num)  # Place Bet covers the number
                for b in player.active_bets
            )
        ]

        # Place bets on the remaining numbers
        bets = []
        for number in numbers:
            min_bet = self.table.get_minimum_bet(number)
            bets.append(PlaceBet(min_bet, player.name, number))

        return bets if bets else None