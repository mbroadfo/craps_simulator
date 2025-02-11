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
        # Convert single bet to a list for uniform handling
        bets = [bet] if not isinstance(bet, list) else bet

        # Calculate the total amount to be wagered
        total_amount = sum(b.amount for b in bets)

        # Check if the player has sufficient funds
        if total_amount > self.balance:
            #print(f"{self.name} has insufficient funds to place ${total_amount} in bets.")
            return False

        # Place each bet and deduct the amount from the player's balance
        for b in bets:
            self.balance -= b.amount
            table.place_bet(b)
            self.active_bets.append(b)

        # Summarize the bets placed
        if len(bets) == 1:
            print(f"{self.name} placed a ${bets[0].amount} {bets[0].bet_type} bet. Bankroll: ${self.balance}")
        else:
            bet_summary = ", ".join(f"{b.bet_type} ${b.amount}" for b in bets)
            print(f"{self.name} bet ${total_amount} on {bet_summary}. Bankroll: ${self.balance}")

        return True

    def resolve_bets(self, table, stats):
        """Resolve all active bets for the player and update the bankroll."""
        # Summarize Won/Lost bets for the player
        won_lost_bets = []
        total_payout = 0

        for bet in self.active_bets:
            if bet.status == "won":
                # Calculate the payout (original bet + profit for Pass-Line, profit only for Place)
                payout = bet.payout()
                total_payout += payout
                won_lost_bets.append(f"{bet.bet_type} bet WON ${payout}")
                self.balance += payout
                stats.total_player_win_loss += payout  # Update player win/loss (total payout)
                stats.total_house_win_loss -= payout  # Update house win/loss (loss of total payout)

                # Remove Pass-Line bets from the table when won
                if bet.bet_type == "Pass Line":
                    self.active_bets.remove(bet)
                # Reset the Place bet status to "active" after winning
                elif bet.bet_type.startswith("Place"):
                    bet.status = "active"
            elif bet.status == "lost":
                won_lost_bets.append(f"{bet.bet_type} bet LOST ${bet.amount}")
                stats.total_player_win_loss -= bet.amount  # Update player win/loss (loss of bet)
                stats.total_house_win_loss += bet.amount  # Update house win/loss (gain of bet)

                # Remove lost bets from the table
                self.active_bets.remove(bet)

        # Print summary of resolved bets
        if won_lost_bets:
            print(f"{self.name}'s resolved bets: {', '.join(won_lost_bets)}. Total Payout: ${total_payout}")

        # Summarize bets still on the table for the player
        active_bets_summary = [
            f"{bet.bet_type}{' (Off)' if bet.status == 'inactive' else ''}"
            for bet in self.active_bets
        ]
        if active_bets_summary:
            print(f"{self.name}'s active bets: {', '.join(active_bets_summary)}")
        else:
            print(f"{self.name} has no active bets.")

        def __str__(self):
            return f"Player: {self.name}, Balance: ${self.balance}"