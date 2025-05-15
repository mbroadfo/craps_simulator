from __future__ import annotations  # Enable forward references for type hints
from typing import TYPE_CHECKING, Optional, List
from craps.bet import Bet
from craps.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from craps.table import Table  # Prevents circular imports
    from craps.rules_engine import RulesEngine
    from craps.game_state import GameState
    from craps.player import Player
    from craps.play_by_play import PlayByPlay
    from craps.base_strategy import BaseStrategy
class IronCrossStrategy(BaseStrategy):
    """Betting strategy for Iron Cross."""

    def __init__(
        self, 
        table: Table, 
        rules_engine: RulesEngine, 
        min_bet: int, 
        play_by_play: PlayByPlay,
        strategy_name: Optional[str] = None,
        play_pass_line: bool = True,
        odds_type: Optional[str] = None,
    ) -> None:
        """
        Initialize the Iron Cross strategy.

        :param table: The table object to determine minimum bets.
        :param rules_engine: The RulesEngine instance from the table.
        :param min_bet: The minimum bet amount for the table.
        :param play_by_play: The play-by-play logging instance.
        """
        super().__init__("Iron Cross")
        self.table: Table = table
        self.rules_engine: RulesEngine = rules_engine
        self.min_bet: int = min_bet
        self.play_by_play: PlayByPlay = play_by_play
        self.strategy_name = strategy_name or "IronCross"
        self.play_pass_line = play_pass_line
        self.odds_type = odds_type

    def place_bets(self, game_state: GameState, player: Player, table: Table) -> List[Bet]:
        """
        Place bets for the Iron Cross strategy.

        :param game_state: The current game state.
        :param player: The player placing the bet.
        :param table: The table where the bet will be placed.
        :return: A list of bets to place, or None if no bets are placed.
        """
        
        rules_engine = self.rules_engine
        bets: List[Bet] = []
        
        if game_state.phase == "come-out":
            if self.play_pass_line:
                if not any(bet.owner == player and bet.bet_type == "Pass Line" for bet in table.bets):
                    bets.append(rules_engine.create_bet("Pass Line", self.min_bet, player))
            return bets

        elif game_state.phase == "point":
            # If Pass Line is active and odds are allowed, place odds bet
            if self.play_pass_line and self.odds_type:
                pass_line_bet = next(
                    (bet for bet in table.bets if bet.owner == player and bet.bet_type == "Pass Line"),
                    None
                )
                if pass_line_bet and not any(
                    bet.owner == player and bet.bet_type == "Pass Line Odds" for bet in table.bets
                ):
                    point = game_state.point
                    multiplier = self.rules_engine.get_odds_multiplier(self.odds_type, point)
                    if multiplier:
                        odds_amount = self.min_bet * multiplier
                        if player.balance >= odds_amount:
                            bets.append(
                                self.rules_engine.create_bet("Pass Line Odds", odds_amount, player)
                            )
            # Reactivate inactive Place bets
            for bet in table.bets:
                if bet.owner == player and bet.bet_type.startswith("Place") and bet.status == "inactive":
                    bet.status = "active"
                    message = f"  🧑{player.name}'s {bet.bet_type} bet is now ON."
                    self.play_by_play.write(message)

            # Place Place bets on 5, 6, and 8 during the point phase (excluding the point number)
            numbers = [5, 6, 8]  # Numbers for the Iron Cross

            # Exclude the point number
            if game_state.point in numbers:
                numbers.remove(game_state.point)

            # Filter out numbers already covered by a Place bet
            numbers = [
                num for num in numbers
                if not any(
                    bet.owner == player and bet.bet_type.startswith("Place") and bet.number == num
                    for bet in table.bets
                )
            ]

            # Use RulesEngine to create Place bets
            for number in numbers:
                min_bet = rules_engine.get_minimum_bet("Place", table, number)
                bets.append(rules_engine.create_bet("Place", min_bet, player, number=number))

            # Add a Field bet if no active Field bet exists
            if not any(bet.owner == player and bet.bet_type == "Field" for bet in table.bets):
                bets.append(rules_engine.create_bet("Field", self.min_bet, player))

            return bets if bets else []

        return []  # No bet to place
