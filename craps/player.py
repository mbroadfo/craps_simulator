# File: .\craps\player.py

from colorama import Fore, Style
from typing import List, Union, Optional, Any
from craps.bet import Bet
from craps.table import Table

class Player:
    def __init__(self, name: str, initial_balance: int = 500, betting_strategy: Any = None, play_by_play: Any = None) -> None:
        """
        Initialize a player.

        :param name: The name of the player.
        :param initial_balance: The initial bankroll of the player.
        :param betting_strategy: The betting strategy used by the player.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        """
        self.name = name
        self.balance = initial_balance
        self.betting_strategy = betting_strategy
        self.play_by_play = play_by_play

    def place_bet(self, bet_type: Union[str, List[str]], amount: Union[int, List[int]], table: Table, phase: str, numbers: List[int] = None) -> bool:
        """
        Place a bet (or multiple bets) on the table and deduct the amount from the player's balance.

        :param bet_type: The type of bet(s) to place.
        :param amount: The amount(s) to wager.
        :param table: The Table object where bets are placed.
        :param phase: The current game phase ("come-out" or "point").
        :param numbers: Optional list of numbers associated with bets (for Place bets, etc.).
        :return: True if all bets were placed successfully, False otherwise.
        """
        rules_engine = table.get_rules_engine()  # ✅ Query Table for RulesEngine

        # Normalize inputs to lists for uniform handling
        bet_types = [bet_type] if isinstance(bet_type, str) else bet_type
        amounts = [amount] if isinstance(amount, int) else amount
        numbers = numbers or [None] * len(bet_types)

        if len(bet_types) != len(amounts):
            raise ValueError("bet_type and amount lists must have the same length.")

        # Create bets using RulesEngine
        bets: List[Bet] = []
        for bt, amt, num in zip(bet_types, amounts, numbers):
            bet = rules_engine.create_bet(bt, amt, self, number=num)
            bets.append(bet)

        # Validate odds bets (must have parent bets already placed)
        for bet in bets:
            if bet.parent_bet and not table.has_bet(bet.parent_bet):
                message = f"{Fore.RED}❌ Cannot place odds bet {bet.bet_type} without a parent bet.{Style.RESET_ALL}"
                self.play_by_play.write(message)
                return False

        # Calculate total bet amount
        total_amount = sum(b.amount for b in bets)

        # Ensure player has sufficient funds
        if total_amount > self.balance:
            message = f"{Fore.RED}❌ {self.name} has insufficient funds to place ${total_amount} in bets.{Style.RESET_ALL}"
            self.play_by_play.write(message)
            return False

        # Place bets on the table
        for bet in bets:
            if not table.place_bet(bet, phase):
                message = f"{Fore.RED}❌ Failed to place {bet.bet_type} bet for {self.name}.{Style.RESET_ALL}"
                self.play_by_play.write(message)
                return False

        # Deduct balance only after successful bet placement
        self.balance -= total_amount
        message = f"{Fore.GREEN}✅ {self.name} placed ${total_amount} in bets. New balance: ${self.balance}.{Style.RESET_ALL}"
        self.play_by_play.write(message)

        return True

    def receive_payout(self, payout: int) -> None:
        """
        Add the payout amount to the player's bankroll.

        :param payout: The payout amount.
        """
        self.balance += payout
        message = f"{Fore.GREEN}✅ {self.name} received a payout of ${payout}. Bankroll: ${self.balance}.{Style.RESET_ALL}"
        self.play_by_play.write(message)  # Write the message to the play-by-play file

    def has_active_bet(self, table: Table, bet_type: str, number: Optional[int] = None) -> bool:
        """
        Check if the player has an active bet of a specific type and number on the table.

        :param table: The table to check for active bets.
        :param bet_type: The type of bet to check for (e.g., "Pass Line", "Place").
        :param number: The number associated with the bet (e.g., 6 for Place 6).
        :return: True if the player has an active bet of the specified type and number, False otherwise.
        """
        return any(
            bet.owner == self and bet.bet_type == bet_type and (number is None or bet.number == number)
            for bet in table.bets
        )