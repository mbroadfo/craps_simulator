"""Wire-format serialization for engine events (Phase 2, Step 0).

One JSON envelope per event: ``{seq, table_id, type, ...payload}`` (D3).
Payload field names come straight from the frozen dataclasses in
``events.py`` — the Python event vocabulary IS the wire schema. ``seq``
and ``table_id`` belong to the envelope and are assigned by the
recorder; they are never event fields.

JSON has no tuples, so deserialization rebuilds the tuple-shaped fields
(dice pairs, per-player pair lists, hop-bet numbers) before
reconstructing the frozen dataclass. Round-tripping any event yields an
equal instance.
"""
from __future__ import annotations
import dataclasses
from typing import Any, Dict, Tuple, Type

from craps.events import Event

ENVELOPE_KEYS = ("seq", "table_id", "type")

#: Tuples of (name, int) pairs, one per player in lineup order.
_PAIR_LIST_FIELDS = frozenset({"bankrolls", "at_risk", "shooter_results"})
#: Two-element tuples: dice outcomes, and hop-bet numbers such as (3, 3).
#: ``number`` may also be a plain int or None, which pass through as-is.
_PAIR_FIELDS = frozenset({"dice", "number"})


def _build_registry() -> Dict[str, Type[Event]]:
    registry: Dict[str, Type[Event]] = {}
    stack = list(Event.__subclasses__())
    while stack:
        cls = stack.pop()
        registry[cls.__name__] = cls
        stack.extend(cls.__subclasses__())
    return registry


EVENT_TYPES: Dict[str, Type[Event]] = _build_registry()


def serialize_event(event: Event, seq: int, table_id: str) -> Dict[str, Any]:
    """Wrap an event in its wire envelope, ready for ``json.dumps``."""
    payload = dataclasses.asdict(event)
    for key in ENVELOPE_KEYS:
        if key in payload:
            raise ValueError(
                f"{type(event).__name__}.{key} collides with an envelope key"
            )
    return {"seq": seq, "table_id": table_id, "type": type(event).__name__, **payload}


def deserialize_event(envelope: Dict[str, Any]) -> Tuple[int, str, Event]:
    """Rebuild ``(seq, table_id, event)`` from a decoded JSON envelope."""
    data = dict(envelope)
    seq = data.pop("seq")
    table_id = data.pop("table_id")
    type_name = data.pop("type")
    cls = EVENT_TYPES.get(type_name)
    if cls is None:
        raise ValueError(f"Unknown event type: {type_name!r}")
    for name, value in data.items():
        if isinstance(value, list):
            if name in _PAIR_LIST_FIELDS:
                data[name] = tuple(tuple(pair) for pair in value)
            elif name in _PAIR_FIELDS:
                data[name] = tuple(value)
    return seq, table_id, cls(**data)
