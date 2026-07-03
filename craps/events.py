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


@dataclass(frozen=True)
class BetResolved(Event):
    player_name: str
    bet_type: str
    amount: int
    number: Optional[Union[int, Tuple[int, int]]]
    status: str
    payout: int


@dataclass(frozen=True)
class PointEstablished(Event):
    point: int


@dataclass(frozen=True)
class PointHit(Event):
    point: int


@dataclass(frozen=True)
class SevenOut(Event):
    shooter_index: int


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
