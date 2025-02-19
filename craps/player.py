# File: .\craps\player.py

from typing import List, Union
from craps.bet import Bet
from craps.table import Table
from craps.game_state import GameState
import logging

class Player:
    def __init__(self, name: str, initial_balance: int = 500, betting_strategy=None):
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

    def place_bet(self, bet: Union[Bet, List[Bet]], table: Table, phase: str) -> bool:
        """
        Place a bet (or multiple bets) on the table and deduct the amount from the player's balance.

        :param bet: The bet(s) to place.
        :param table: The table to place the bet on.
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet(s) were placed successfully, False otherwise.
        """
        # Convert single bet to a list for uniform handling
        bets = [bet] if not isinstance(bet, list) else bet

        # Calculate the total amount to be wagered
        total_amount = sum(b.amount for b in bets)

        # Check if the player has sufficient funds
        if total_amount > self.balance:
            logging.warning(f"{self.name} has insufficient funds to place ${total_amount} in bets.")
            return False

        # Place each bet on the table
        successful_bets = []
        for b in bets:
            if not table.place_bet(b, phase):  # Use the updated place_bet method
                logging.warning(f"Failed to place {b.bet_type} bet for {self.name}.")
                return False

            # Deduct the amount from the player's balance
            self.balance -= b.amount
            self.active_bets.append(b)
            successful_bets.append(b)

        # Summarize the bets placed
        if len(successful_bets) == 1:
            logging.info(f"{self.name} placed a ${successful_bets[0].amount} {successful_bets[0].bet_type} bet. Bankroll: ${self.balance}.")
        else:
            bet_summary = ", ".join(f"{b.bet_type} ${b.amount}" for b in successful_bets)
            logging.info(f"{self.name} placed ${total_amount} on {bet_summary}. Bankroll: ${self.balance}.")

        return True
    
    def clear_resolved_bets(self) -> None:
        """
        Remove all resolved bets (won or lost) from the player's active bets.
        """
        self.active_bets = [bet for bet in self.active_bets if not bet.is_resolved()]
        logging.info(f"{self.name} has {len(self.active_bets)} active bets after clearing resolved bets.")

    def take_actions_after_roll(self, game_state: GameState, table: Table) -> None:
        """
        Take actions after a roll based on the game state and betting strategy.

        :param game_state: The current game state.
        :param table: The table to interact with.
        """
        if self.betting_strategy:
            # Let the betting strategy decide what actions to take
            new_bets = self.betting_strategy.get_bet(game_state, self)
            if new_bets:
                self.place_bet(new_bets, table, game_state.phase)  # Pass the current phase