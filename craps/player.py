# File: .\craps\player.py

from craps.bet import Bet

class Player:
    def __init__(self, name, initial_balance=500, betting_strategy=None):
        """
        Initialize a player.
        
        :param name: The name of the player.
        :param initial_balance: The initial bankroll of the player.
        :param betting_strategy: The betting strategy used by the player.
        """
        self.name = name
        self.balance = initial_balance
        self.betting_strategy = betting_strategy
        self.active_bets = []  # Track active bets for this player

    def place_bet(self, bet, table):
        """Place a bet (or multiple bets) on the table and deduct the amount from the player's balance."""
        if isinstance(bet, list):  # Handle multiple bets
            for b in bet:
                self._place_single_bet(b, table)
        else:  # Handle a single bet
            self._place_single_bet(bet, table)

    def _place_single_bet(self, bet, table):
        """Place a single bet on the table and deduct the amount from the player's balance."""
        if bet.amount > self.balance:
            # print(f"{self.name} has insufficient funds to place a ${bet.amount} bet.")
            return False
        
        self.balance -= bet.amount
        table.place_bet(bet)
        self.active_bets.append(bet)
        print(f"{self.name} placed a ${bet.amount} {bet.bet_type} bet. Bankroll: ${self.balance}")
        return True

    def resolve_bets(self, table, stats):
        """Resolve all active bets for the player and update the bankroll."""
        for bet in self.active_bets:
            if bet.status == "won":
                # Calculate the total payout (original bet + profit)
                payout = bet.payout()
                self.balance += payout
                stats.update_player_win_loss(payout - bet.amount)  # Update player win/loss (profit only)
                stats.update_house_win_loss(-(payout - bet.amount))  # Update house win/loss (loss of profit only)
                print(f"{self.name} WON ${payout} on a ${bet.amount} {bet.bet_type} bet. Bankroll: ${self.balance}")
            elif bet.status == "lost":
                stats.update_player_win_loss(-bet.amount)  # Update player win/loss (loss of bet)
                stats.update_house_win_loss(bet.amount)  # Update house win/loss (gain of bet)
                print(f"{self.name} LOST a ${bet.amount} {bet.bet_type} bet. Bankroll: ${self.balance}")

        # Remove resolved bets (won or lost) from the active bets list
        self.active_bets = [bet for bet in self.active_bets if bet.status in ["active", "inactive"]]

    def __str__(self):
        return f"Player: {self.name}, Balance: ${self.balance}"