# File: .\craps\player.py

from typing import List, Union
from craps.bet import Bet
from craps.table import Table
from craps.game_state import GameState
from craps.log_manager import LogManager
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
        for b in bets:
            if not table.place_bet(b, phase):  # Use the updated place_bet method
                logging.warning(f"Failed to place {b.bet_type} bet for {self.name}.")
                return False

            # Deduct the amount from the player's balance
            self.balance -= b.amount
            logging.info(LogManager.format_log_message(f"{self.name} placed a ${b.amount} {b.bet_type} bet. Bankroll: ${self.balance}."))

        return True

    def receive_payout(self, payout: int) -> None:
        """
        Add the payout amount to the player's bankroll.

        :param payout: The payout amount.
        """
        self.balance += payout
        logging.info(LogManager.format_log_message(f"{self.name} received a payout of ${payout}. Bankroll: ${self.balance}."))

    def has_active_bet(self, table: Table, bet_type: str) -> bool:
        """
        Check if the player has an active bet of a specific type on the table.

        :param table: The table to check for active bets.
        :param bet_type: The type of bet to check for (e.g., "Pass Line").
        :return: True if the player has an active bet of the specified type, False otherwise.
        """
        return any(bet.owner == self and bet.bet_type == bet_type for bet in table.bets)