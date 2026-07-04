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
    parent_number: BetNumber = None
    hits: int = 0
    payout: int = 0
    unit: int = 1


@dataclass(frozen=True)
class TableView:
    """Immutable snapshot of everything a strategy may consider.

    ``stage`` is "place" when the engine is accepting new bets before a roll
    and "adjust" after resolution (the v1 ``adjust_bets`` hook). In the
    adjust stage the adapter only applies amount changes to live bets —
    new bets returned there are ignored, mirroring the v1 engine, which
    discards ``adjust_bets`` return values.
    """
    phase: str
    point: Optional[int]
    previous_point: Optional[int]
    bankroll: int
    bets: Tuple[BetView, ...]
    table_minimum: int
    table_maximum: int
    stage: str = "place"
    puck_on: bool = False
    all_completed: bool = False
    tall_completed: bool = False
    small_completed: bool = False
    last_roll_total: Optional[int] = None

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
    """A bet the strategy wants placed (place stage) or reshaped (adjust stage).

    ``odds_on`` names the parent bet type for odds bets (e.g. "Pass Line");
    the adapter links the live parent bet when compiling — matching on
    ``number`` too when set, so odds can target a specific Come bet. Odds
    specs are created without a number and have it assigned post-creation,
    mirroring how v1 strategies build them.

    In the adjust stage a spec addresses the live bet matching (bet_type,
    number): ``amount`` is the desired final amount and ``set_status``, if
    given, the desired status. Specs with no live match are ignored there.
    """
    bet_type: str
    amount: int
    number: BetNumber = None
    odds_on: Optional[str] = None
    set_status: Optional[str] = None


Layout = Tuple[BetSpec, ...]


def flat_bet_minimum(table_minimum: int, number: Optional[int]) -> int:
    """Place/Buy/Lay minimum per RulesEngine.get_minimum_bet: 6 and 8 bet in
    units of table_min + table_min//5 (e.g. $12 on a $10 table), others at
    the table minimum."""
    if number in (6, 8):
        return table_minimum + (table_minimum // 5)
    return table_minimum


class ContractStrategy(ABC):
    """Base class for v2 strategies. Implementations must be pure: no I/O,
    no engine object access — state across rolls travels in the memo."""

    name: str = "Unnamed v2"

    @abstractmethod
    def wants(self, view: TableView, memo: Any) -> Tuple[Layout, Any]:
        """Return the bets to place this call and the next memo."""

    def new_shooter_memo(self, memo: Any) -> Any:
        """Return the memo for a fresh shooter (v1 on_new_shooter hook)."""
        return memo


def build_table_view(game_state: GameState, player: Player, table: "Table", stage: str = "place") -> TableView:
    own_bets = tuple(
        BetView(
            bet_type=b.bet_type,
            amount=b.amount,
            number=b.number,
            status=b.status,
            parent_type=b.parent_bet.bet_type if b.parent_bet is not None else None,
            parent_number=b.parent_bet.number if b.parent_bet is not None else None,
            hits=getattr(b, "hits", 0),
            payout=b.resolved_payout,
            unit=b.unit or 1,
        )
        for b in table.bets if b.owner == player
    )
    stats = getattr(game_state, "stats", None)
    return TableView(
        phase=game_state.phase,
        point=game_state.point,
        previous_point=game_state.previous_point,
        bankroll=player.balance,
        bets=own_bets,
        table_minimum=table.house_rules.table_minimum,
        table_maximum=table.house_rules.table_maximum,
        stage=stage,
        puck_on=game_state.puck_on,
        all_completed=game_state.all_completed,
        tall_completed=game_state.tall_completed,
        small_completed=game_state.small_completed,
        last_roll_total=getattr(stats, "last_roll_total", None) if stats is not None else None,
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

    @property
    def turned_off(self) -> bool:
        """Mirrored for CrapsEngine.refresh_bet_statuses, which reads
        getattr(strategy, "turned_off", False) off the strategy object."""
        return bool(getattr(self.contract, "turned_off", False))

    def place_bets(self, game_state: GameState, player: Player, table: "Table") -> List[Bet]:
        view = build_table_view(game_state, player, table)
        layout, self._memo = self.contract.wants(view, self._memo)

        bets: List[Bet] = []
        for spec in layout:
            if spec.set_status is not None:
                # Status spec: reshape a live bet (e.g. reactivation), place nothing
                live = next(
                    (b for b in table.bets
                     if b.owner == player and b.bet_type == spec.bet_type and b.number == spec.number),
                    None,
                )
                if live is not None and live.status != spec.set_status:
                    live.status = spec.set_status
                continue
            if spec.odds_on is not None:
                parent = next(
                    (b for b in table.bets
                     if b.owner == player and b.bet_type == spec.odds_on
                     and (spec.number is None or b.number == spec.number)),
                    None,
                )
                if parent is None:
                    continue  # No live parent bet to attach odds to
                # v1 strategies create odds without a number and assign it
                # afterward (bypassing create_bet validation) — mirror that
                # so the constructed Bet is identical.
                bet = table.rules_engine.create_bet(
                    spec.bet_type, spec.amount, player, parent_bet=parent,
                )
                if spec.number is not None:
                    bet.number = spec.number
            else:
                bet = table.rules_engine.create_bet(
                    spec.bet_type, spec.amount, player, number=spec.number,
                )
            bets.append(bet)
        return bets

    def adjust_bets(self, game_state: GameState, player: Player, table: "Table") -> Optional[List[Bet]]:
        """v1 adjust_bets hook: apply amount changes to live bets.

        Specs that match a live bet (type + number) with a different amount
        are applied in place — the v1 pressing/regression mechanic. Specs
        with no live match are ignored, mirroring the v1 engine discarding
        adjust_bets return values.
        """
        view = build_table_view(game_state, player, table, stage="adjust")
        layout, self._memo = self.contract.wants(view, self._memo)

        changed: List[Bet] = []
        for spec in layout:
            live = next(
                (b for b in table.bets
                 if b.owner == player and b.bet_type == spec.bet_type and b.number == spec.number),
                None,
            )
            if live is None:
                continue
            if live.amount != spec.amount:
                live.amount = spec.amount
                changed.append(live)
            if spec.set_status is not None and live.status != spec.set_status:
                live.status = spec.set_status
                if live not in changed:
                    changed.append(live)
        return changed or None

    def on_new_shooter(self) -> None:
        self._memo = self.contract.new_shooter_memo(self._memo)
