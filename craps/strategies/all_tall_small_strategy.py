from typing import Optional, List, TYPE_CHECKING
from craps.base_strategy import BaseStrategy
from craps.rules_engine import RulesEngine
from craps.play_by_play import PlayByPlay
from craps.player import Player
from craps.bet import Bet
from craps.game_state import GameState

if TYPE_CHECKING:
    from craps.table import Table

ATS_TYPE_MAP = {
    "AllTallSmall": ["All", "Tall", "Small"],
    "TallSmall": ["Tall", "Small"],
    "All": ["All"],
    "Tall": ["Tall"],
    "Small": ["Small"],
}

class AllTallSmallStrategy(BaseStrategy):
    def __init__(
        self,
        table: "Table",
        rules_engine: RulesEngine,
        play_by_play: Optional[PlayByPlay] = None,
        ats_type: str = "AllTallSmall",
        bet_amount: Optional[int] = None,
        strategy_name: Optional[str] = None,
    ):
        super().__init__("AllTallSmall")
        
        self.table = table
        self.rules_engine = rules_engine
        self.play_by_play = play_by_play
        self.ats_type = ats_type
        self.ats_components = ATS_TYPE_MAP[ats_type]
        self.bet_amount = bet_amount
        self.strategy_name = strategy_name or "AllTallSmall"

    def place_bets(
        self, game_state: GameState, player: Player, table: "Table"
    ) -> List[Bet]:
        placed_bets: List[Bet] = []

        if game_state.phase != "come-out":
            return []

        bet_amount = self.bet_amount or self.rules_engine.get_minimum_bet("All", table)

        for ats_type in self.ats_components:
            # Skip if already completed this shooter
            if ats_type == "All" and game_state.all_completed:
                continue
            if ats_type == "Tall" and game_state.tall_completed:
                continue
            if ats_type == "Small" and game_state.small_completed:
                continue

            if not player.has_active_bet(table, ats_type):
                bet = self.rules_engine.create_bet(ats_type, bet_amount, player)
                placed_bets.append(bet)

        return placed_bets

