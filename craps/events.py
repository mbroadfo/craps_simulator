from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Type, Union


@dataclass(frozen=True)
class Event:
    """Base class for all engine events."""


@dataclass(frozen=True)
class SessionStarted(Event):
    num_shooters: int


@dataclass(frozen=True)
class ShooterAssigned(Event):
    shooter_index: int
    shooter_name: str


@dataclass(frozen=True)
class BetsRequested(Event):
    """The engine is about to collect bets from strategies."""


@dataclass(frozen=True)
class BetPlaced(Event):
    player_name: str
    bet_type: str
    amount: int
    number: Optional[Union[int, Tuple[int, int]]]


@dataclass(frozen=True)
class DiceRolled(Event):
    shooter_index: int
    roll_number: int
    dice: Tuple[int, int]
    total: int
    phase: str
    point: Optional[int]
    table_risk: int = 0
    shooter_name: str = ""


@dataclass(frozen=True)
class BetResolved(Event):
    player_name: str
    bet_type: str
    amount: int
    number: Optional[Union[int, Tuple[int, int]]]
    status: str
    payout: int
    #: Bet.payout() at resolution time — what the stats ledger credits on a
    #: win (may include the returned stake for contract bets).
    win_payout: int = 0
    #: Whether settlement took the bet off the table. Winning non-contract
    #: bets can stay up ("if it pays, it stays" per house rules); the felt
    #: must not have to know that rule — the engine states the fact.
    removed: bool = False


@dataclass(frozen=True)
class BetMoved(Event):
    """A bet acquired its number after placement: Come/Don't Come travel,
    or an odds bet attaching to the established point."""
    player_name: str
    bet_type: str
    amount: int
    number: int


@dataclass(frozen=True)
class BetAdjusted(Event):
    """A live bet was reshaped between rolls (pressing/regression or an
    on/off flip requested by the strategy)."""
    player_name: str
    bet_type: str
    amount: int
    number: Optional[Union[int, Tuple[int, int]]]
    status: str


@dataclass(frozen=True)
class BetStatusChanged(Event):
    """A live bet's working status changed outside resolution (phase
    refresh or a strategy status spec at bet-collection time)."""
    player_name: str
    bet_type: str
    number: Optional[Union[int, Tuple[int, int]]]
    status: str


@dataclass(frozen=True)
class NumberHit(Event):
    """ATS tracking recorded a number this roll (message pre-formatted)."""
    total: int
    message: str


@dataclass(frozen=True)
class GameStateChanged(Event):
    """Phase/point transition after resolution (message pre-formatted)."""
    message: str


@dataclass(frozen=True)
class BankrollsUpdated(Event):
    """Per-player bankrolls after post-roll adjustments, in lineup order."""
    bankrolls: Tuple[Tuple[str, int], ...]


@dataclass(frozen=True)
class RiskUpdated(Event):
    """Per-player active amounts at risk after status refresh, in lineup order."""
    at_risk: Tuple[Tuple[str, int], ...]


@dataclass(frozen=True)
class PointEstablished(Event):
    point: int


@dataclass(frozen=True)
class PointHit(Event):
    point: int


@dataclass(frozen=True)
class SevenOut(Event):
    shooter_index: int
    #: Per-player bankroll delta over this shooter's hand, in lineup order.
    shooter_results: Tuple[Tuple[str, int], ...] = ()


@dataclass(frozen=True)
class SessionFinalized(Event):
    session_rolls: int


EventHandler = Callable[[Event], None]


class EventBus:
    """Minimal synchronous pub/sub bus.

    Handlers subscribe by event class and receive every published event of
    that class or any subclass — subscribing to ``Event`` observes the full
    stream. Dispatch is synchronous and in subscription order, keeping
    session runs deterministic.
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}

    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for cls in type(event).__mro__:
            if cls is object:
                continue
            for handler in self._handlers.get(cls, ()):
                handler(event)
