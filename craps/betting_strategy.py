class BettingStrategy:
    """Base class for all betting strategies."""
    def __init__(self, min_bet):
        self.min_bet = min_bet

    def get_bet(self, game_state, player):
        """Determine the bet to place based on the game state and player."""
        raise NotImplementedError("Subclasses must implement this method.")


class PassLineStrategy(BettingStrategy):
    """Betting strategy for Pass Line bets."""
    def __init__(self, min_bet):
        super().__init__(min_bet)
        self.has_bet = False  # Track if the player has an active Pass Line bet

    def get_bet(self, game_state, player):
        """Place a Pass Line bet during the come-out roll if no active bet exists."""
        if game_state.phase == "come-out":
            if not self.has_bet:
                self.has_bet = True
                return {"bet_type": "Pass Line", "amount": self.min_bet}
            else:
                # Reset the bet flag if the previous bet was resolved (win or lose)
                self.has_bet = False
                return {"bet_type": "Pass Line", "amount": self.min_bet}
        return None  # No bet to place  