"""Strategy contract v2: pure strategies over immutable table snapshots.

A v2 strategy implements ``wants(view, memo) -> (layout, memo)``: given a
frozen ``TableView``, return the ``BetSpec``s it wants placed this call plus
an opaque memo carried to the next call. Strategies never touch ``Table``,
``RulesEngine`` instances, or logging — that is what makes them small,
testable, and safe to generate.

``V2StrategyAdapter`` bridges a v2 strategy into the existing ``BaseStrategy``
engine path. The adapter deliberately does NOT dedupe or reorder specs:
existence checks belong in ``wants()`` (mirroring how v1 strategies guard
with ``has_active_bet``), so a v2 port stays roll-for-roll identical to its
v1 original under the regression harness.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Union, TYPE_CHECKING

from craps.base_strategy import BaseStrategy
from craps.bet import Bet
from craps.game_state import GameState
from craps.player import Player

if TYPE_CHECKING:
    from craps.table import Table

BetNumber = Union[int, Tuple[int, int], None]


@dataclass(frozen=True)
class BetView:
    """Read-only snapshot of one of the player's live bets."""
    bet_type: str
    amount: int
    number: BetNumber
    status: str
    parent_type: Optional[str]


@dataclass(frozen=True)
class TableView:
    """Immutable snapshot of everything a strategy may consider."""
    phase: str
    point: Optional[int]
    previous_point: Optional[int]
    bankroll: int
    bets: Tuple[BetView, ...]
    table_minimum: int
    table_maximum: int

    def has(self, bet_type: str, number: Optional[int] = None) -> bool:
        """Mirror of Player.has_active_bet against the snapshot."""
        return any(
            b.bet_type == bet_type and (number is None or b.number == number)
            for b in self.bets
        )

    def get(self, bet_type: str) -> Optional[BetView]:
        return next((b for b in self.bets if b.bet_type == bet_type), None)


@dataclass(frozen=True)
class BetSpec:
    """A bet the strategy wants placed on this call.

    ``odds_on`` names the parent bet type for odds bets (e.g. "Pass Line");
    the adapter links the live parent bet when compiling.
    """
    bet_type: str
    amount: int
    number: BetNumber = None
    odds_on: Optional[str] = None


Layout = Tuple[BetSpec, ...]


class ContractStrategy(ABC):
    """Base class for v2 strategies. Implementations must be pure: no I/O,
    no engine object access — state across rolls travels in the memo."""

    name: str = "Unnamed v2"

    #: Reactivate the player's inactive Place bets during the point phase
    #: before placing new bets (v1 Iron Cross behavior).
    reactivates_place_bets: bool = False

    @abstractmethod
    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        """Return the bets to place this call and the next memo."""


def build_table_view(game_state: GameState, player: Player, table: "Table") -> TableView:
    own_bets = tuple(
        BetView(
            bet_type=b.bet_type,
            amount=b.amount,
            number=b.number,
            status=b.status,
            parent_type=b.parent_bet.bet_type if b.parent_bet is not None else None,
        )
        for b in table.bets if b.owner == player
    )
    return TableView(
        phase=game_state.phase,
        point=game_state.point,
        previous_point=game_state.previous_point,
        bankroll=player.balance,
        bets=own_bets,
        table_minimum=table.house_rules.table_minimum,
        table_maximum=table.house_rules.table_maximum,
    )


class V2StrategyAdapter(BaseStrategy):
    """Runs a ContractStrategy inside the v1 BaseStrategy engine path.

    One adapter per player: the memo is per-instance state.
    """

    def __init__(self, contract: ContractStrategy, strategy_name: Optional[str] = None) -> None:
        super().__init__(contract.name)
        self.contract = contract
        self.strategy_name = strategy_name or contract.name
        self._memo: Any = None

    def place_bets(self, game_state: GameState, player: Player, table: "Table") -> List[Bet]:
        if self.contract.reactivates_place_bets and game_state.phase == "point":
            for bet in table.bets:
                if bet.owner == player and bet.bet_type.startswith("Place") and bet.status == "inactive":
                    bet.status = "active"

        view = build_table_view(game_state, player, table)
        layout, self._memo = self.contract.wants(view, self._memo)

        bets: List[Bet] = []
        for spec in layout:
            parent: Optional[Bet] = None
            if spec.odds_on is not None:
                parent = next(
                    (b for b in table.bets if b.owner == player and b.bet_type == spec.odds_on),
                    None,
                )
                if parent is None:
                    continue  # No live parent bet to attach odds to
            bets.append(table.rules_engine.create_bet(
                spec.bet_type, spec.amount, player, number=spec.number, parent_bet=parent,
            ))
        return bets

    def on_new_shooter(self) -> None:
        pass  # memo persists across shooters unless the strategy resets it via wants()
