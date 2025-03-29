from colorama import Fore, Style
from typing import List, Union, Optional, Any, Tuple, TYPE_CHECKING
from craps.bet import Bet
from craps.play_by_play import PlayByPlay
import random

if TYPE_CHECKING:
    from craps.table import Table
    
class Player:
    def __init__(self, name: str, initial_balance: int = 500, betting_strategy: Optional[Any] = None):
        """
        Initialize a player.

        :param name: The name of the player.
        :param initial_balance: The initial bankroll of the player.
        :param betting_strategy: The betting strategy used by the player.
        """
        self.name: str = name
        self.balance: int = initial_balance
        self.betting_strategy: Any = betting_strategy
        self.is_shooter: bool = False

    def place_bet(self, bet: Union[Bet, List[Bet]], table: "Table", phase: str, play_by_play: PlayByPlay) -> bool:
        """
        Place a bet (or multiple bets) on the table and deduct the amount from the player's balance.

        :param bet: The bet(s) to place.
        :param table: The table to place the bet on.
        :param phase: The current game phase ("come-out" or "point").
        :param play_by_play: The PlayByPlay instance for logging messages.
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
            message: str = f"  ❌ {self.name} has insufficient funds to place ${total_amount} in bets.{Style.RESET_ALL}"
            if play_by_play:
                play_by_play.write(message)
            return False

        for b in bets:
            if not table.place_bet(b, phase):
                message = f"  ❌ Failed to place {b.bet_type} bet for {self.name}.{Style.RESET_ALL}"
                if play_by_play:
                    play_by_play.write(message)
                return False

            if play_by_play:
                risk = self.get_total_at_risk(table)
                message = (
                    f"  ✅ Bet placed: {self.name}'s ${b.amount} {b.bet_type} bet "
                    f"(Status: {b.status}). Bankroll: ${self.balance} (w/ ${risk} on the table)"
                )
                play_by_play.write(message)


        return True

    def receive_payout(self, payout: int, play_by_play: PlayByPlay) -> None:
        """
        Add the payout amount to the player's bankroll.

        :param payout: The payout amount.
        """
        self.balance += payout

    def has_active_bet(self, table: "Table", bet_type: str, number: Optional[int] = None) -> bool:
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

    def roll_dice(self) -> Tuple[int, int]:
        """
        Roll the dice if this player is the shooter.

        :return: A tuple representing the dice roll (e.g., (3, 4)).
        """
        if self.is_shooter:
            return random.randint(1, 6), random.randint(1, 6)
        else:
            raise ValueError(f"{self.name} is not the shooter and cannot roll dice.")

    def reset_shooter(self) -> None:
        """
        Reset the shooter status when a new round begins.
        """
        self.is_shooter = False

    def has_odds_bets(self, table: "Table") -> bool:
        """Check if the player has any active Come Odds bets."""
        return any(bet.bet_type == "Come Odds" and bet.status == "active" for bet in table.bets if bet.owner == self)

    def update_come_odds_status(self, table: "Table", should_work: bool) -> None:
        """Update the status of the player's Come Odds bets based on strategy preference."""
        for bet in table.bets:
            if bet.owner == self and bet.bet_type == "Come Odds":
                bet.status = "active" if should_work else "inactive"

    def get_total_at_risk(self, table: "Table") -> int:
        """Return the total amount this player has at risk on the table."""
        return sum(bet.amount for bet in table.bets if bet.owner == self)
    
    def win_bet(self, bet: Bet, play_by_play: PlayByPlay) -> None:
        winnings = bet.payout()
        self.balance += winnings
        play_by_play.write(
            f"  ✅ {self.name}'s {bet.bet_type} bet WON ${winnings}! New Bankroll: ${self.balance}"
        )

    def lose_bet(self, bet: Bet, play_by_play: PlayByPlay) -> None:
        self.balance -= bet.amount
        play_by_play.write(
            f"  ❌ {self.name}'s {bet.bet_type} bet LOST ${bet.amount}. New Bankroll: ${self.balance}"
        )
