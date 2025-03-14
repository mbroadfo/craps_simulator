from colorama import Fore, Style
from typing import List, Union, Optional, Any
from craps.bet import Bet
from craps.table import Table
from craps.play_by_play import PlayByPlay

class Player:
    def __init__(self, name: str, initial_balance: int = 500, betting_strategy: Any = None, play_by_play: Optional[PlayByPlay] = None) -> None:
        """
        Initialize a player.

        :param name: The name of the player.
        :param initial_balance: The initial bankroll of the player.
        :param betting_strategy: The betting strategy used by the player.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        """
        self.name: str = name
        self.balance: int = initial_balance
        self.betting_strategy: Any = betting_strategy
        self.play_by_play: Optional[PlayByPlay] = play_by_play

    def place_bet(self, bet: Union[Bet, List[Bet]], table: Table, phase: str) -> bool:
        """
        Place a bet (or multiple bets) on the table and deduct the amount from the player's balance.

        :param bet: The bet(s) to place.
        :param table: The table to place the bet on.
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet(s) were placed successfully, False otherwise.
        """
        bets: List[Bet] = [bet] if not isinstance(bet, list) else bet

        for b in bets:
            if hasattr(b, 'parent_bet') and b.parent_bet is not None:
                if b.parent_bet.owner != self:
                    raise ValueError("Cannot place odds bet on another player's bet")
                if not table.has_bet(b.parent_bet):
                    raise ValueError("Parent bet must be on the table before placing odds")

        total_amount: int = sum(b.amount for b in bets)

        if total_amount > self.balance:
            message: str = f"{Fore.RED}❌ {self.name} has insufficient funds to place ${total_amount} in bets.{Style.RESET_ALL}"
            if self.play_by_play:
                self.play_by_play.write(message)
            return False

        for b in bets:
            if not table.place_bet(b, phase):
                message = f"{Fore.RED}❌ Failed to place {b.bet_type} bet for {self.name}.{Style.RESET_ALL}"
                if self.play_by_play:
                    self.play_by_play.write(message)
                return False

            message = f"{Fore.GREEN}✅ {self.name} placed a ${b.amount} {b.bet_type} bet. Bankroll: ${self.balance}.{Style.RESET_ALL}"
            if self.play_by_play:
                self.play_by_play.write(message)

        return True

    def receive_payout(self, payout: int) -> None:
        """
        Add the payout amount to the player's bankroll.

        :param payout: The payout amount.
        """
        self.balance += payout
        message: str = f"{Fore.GREEN}✅ {self.name} received a payout of ${payout}. Bankroll: ${self.balance}.{Style.RESET_ALL}"
        if self.play_by_play:
            self.play_by_play.write(message)

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
