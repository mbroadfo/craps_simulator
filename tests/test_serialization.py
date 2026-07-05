"""Wire-format round-trip tests for every event type (Phase 2, Step 0)."""
import json

import pytest

from craps.events import (
    BankrollsUpdated,
    BetAdjusted,
    BetMoved,
    BetPlaced,
    BetResolved,
    BetStatusChanged,
    BetsRequested,
    DiceRolled,
    Event,
    GameStateChanged,
    NumberHit,
    PointEstablished,
    PointHit,
    RiskUpdated,
    SessionFinalized,
    SessionStarted,
    SevenOut,
    ShooterAssigned,
)
from craps.serialization import EVENT_TYPES, deserialize_event, serialize_event

ONE_OF_EACH = [
    SessionStarted(num_shooters=10),
    ShooterAssigned(shooter_index=1, shooter_name="Linus"),
    BetsRequested(),
    BetPlaced(player_name="Linus", bet_type="Pass Line", amount=10, number=None),
    BetPlaced(player_name="Hardy", bet_type="Hop", amount=1, number=(3, 3)),
    BetPlaced(player_name="Sixer", bet_type="Place", amount=12, number=6),
    DiceRolled(
        shooter_index=0,
        roll_number=7,
        dice=(4, 3),
        total=7,
        phase="point",
        point=6,
        table_risk=44,
        shooter_name="Linus",
    ),
    BetResolved(
        player_name="Linus",
        bet_type="Pass Line",
        amount=10,
        number=None,
        status="lost",
        payout=0,
        win_payout=0,
    ),
    BetResolved(
        player_name="Hardy",
        bet_type="Hop",
        amount=1,
        number=(3, 3),
        status="won",
        payout=30,
        win_payout=31,
        removed=True,
    ),
    BetMoved(player_name="Molly", bet_type="Come", amount=10, number=6),
    BetAdjusted(
        player_name="Go Big", bet_type="Place", amount=12, number=6,
        status="active",
    ),
    BetStatusChanged(
        player_name="Sixer", bet_type="Place", number=8, status="inactive",
    ),
    NumberHit(total=6, message="  🎯 6 recorded"),
    GameStateChanged(message="  ➡️ point established"),
    BankrollsUpdated(bankrolls=(("Linus", 490), ("Hardy", 501))),
    RiskUpdated(at_risk=(("Linus", 10), ("Hardy", 0))),
    PointEstablished(point=6),
    PointHit(point=6),
    SevenOut(shooter_index=1, shooter_results=(("Linus", -20), ("Hardy", 5))),
    SessionFinalized(session_rolls=120),
]


def test_registry_covers_every_event_type():
    subclasses = set()
    stack = list(Event.__subclasses__())
    while stack:
        cls = stack.pop()
        subclasses.add(cls)
        stack.extend(cls.__subclasses__())
    assert set(EVENT_TYPES.values()) == subclasses


@pytest.mark.parametrize("event", ONE_OF_EACH, ids=lambda e: type(e).__name__)
def test_round_trip_through_json(event):
    envelope = serialize_event(event, seq=3, table_id="table-1")
    assert envelope["seq"] == 3
    assert envelope["table_id"] == "table-1"
    assert envelope["type"] == type(event).__name__

    wire = json.dumps(envelope)
    seq, table_id, rebuilt = deserialize_event(json.loads(wire))

    assert seq == 3
    assert table_id == "table-1"
    assert rebuilt == event
    assert type(rebuilt) is type(event)


def test_every_event_type_exercised_by_round_trip_cases():
    assert {type(e).__name__ for e in ONE_OF_EACH} == set(EVENT_TYPES)


def test_payload_field_names_match_dataclass_fields():
    event = ONE_OF_EACH[6]  # DiceRolled — the widest event
    envelope = serialize_event(event, seq=0, table_id="t")
    payload_keys = set(envelope) - {"seq", "table_id", "type"}
    assert payload_keys == {
        "shooter_index", "roll_number", "dice", "total",
        "phase", "point", "table_risk", "shooter_name",
    }


def test_unknown_event_type_rejected():
    with pytest.raises(ValueError, match="Unknown event type"):
        deserialize_event({"seq": 0, "table_id": "t", "type": "NotAnEvent"})
