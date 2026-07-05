"""Chip-fidelity events (Phase 2, Step 2 core): the event stream alone
must be able to drive every chip on a felt — placement, travel,
press/regress, on/off flips, and removal.

The ChipTracker here is the Python twin of the web client's reducer: it
maintains chips purely from events and fails on any orphan (an event
referencing a chip the stream never placed). The contract the TS
reducer must implement:

- Chips are a MULTISET keyed by (player, bet_type, number) — stacks of
  amounts. Two Come bets can legitimately occupy the same number (one
  sits on 8, the next travels there), so a unique key cannot represent
  the felt.
- Events that reference a numbered chip fall back to the un-numbered
  (player, bet_type, None) stack when the exact key misses — bets whose
  number was filled at resolution time (odds settled the same roll they
  attached, the Field win-number quirk).
- Within a stack, instances match by amount when possible, else any
  instance (visually indistinguishable on a stack).
"""
from typing import Dict, List, Optional, Tuple, Union

import pytest

from craps.events import (
    BetAdjusted,
    BetMoved,
    BetPlaced,
    BetResolved,
    BetStatusChanged,
    Event,
)
from craps.table_runner import TableRunner

LINEUP = [
    ("Molly", "3-Point Molly"),        # Come bets → BetMoved
    ("Go Big", "RegressHalfPress"),    # regression → BetAdjusted
    ("Hardy", "HardwayHighway"),       # hardways stay-up / reactivation
    ("Fielder", "Field"),              # field, incl. its win-number quirk
]

Key = Tuple[str, str, Optional[Union[int, Tuple[int, int]]]]


class ChipTracker:
    """Chips-on-felt state derived from events only (amount multiset)."""

    def __init__(self) -> None:
        self.chips: Dict[Key, List[int]] = {}
        self.orphans: list = []

    def _find(
        self, player: str, bet_type: str,
        number: Optional[Union[int, Tuple[int, int]]],
    ) -> Optional[Key]:
        exact: Key = (player, bet_type, number)
        if self.chips.get(exact):
            return exact
        fallback: Key = (player, bet_type, None)
        if self.chips.get(fallback):
            return fallback
        return None

    def _push(self, key: Key, amount: int) -> None:
        self.chips.setdefault(key, []).append(amount)

    def _pop(self, key: Key, amount: int) -> None:
        stack = self.chips[key]
        stack.remove(amount) if amount in stack else stack.pop()
        if not stack:
            del self.chips[key]

    def apply(self, e: Event) -> None:
        if isinstance(e, BetPlaced):
            self._push((e.player_name, e.bet_type, e.number), e.amount)
        elif isinstance(e, BetMoved):
            source = self._find(e.player_name, e.bet_type, None)
            if source is None:
                self.orphans.append(e)
                return
            self._pop(source, e.amount)
            self._push((e.player_name, e.bet_type, e.number), e.amount)
        elif isinstance(e, BetAdjusted):
            key = self._find(e.player_name, e.bet_type, e.number)
            if key is None:
                self.orphans.append(e)
                return
            self.chips[key].pop()
            self.chips[key].append(e.amount)
        elif isinstance(e, BetStatusChanged):
            if self._find(e.player_name, e.bet_type, e.number) is None:
                self.orphans.append(e)
        elif isinstance(e, BetResolved):
            key = self._find(e.player_name, e.bet_type, e.number)
            if key is None:
                self.orphans.append(e)
                return
            if e.removed:
                self._pop(key, e.amount)


@pytest.fixture(scope="module")
def captured():
    runner = TableRunner(
        table_id="chip-events",
        players=LINEUP,
        max_shooters=20,
        dice_seed=20260705,
    )
    events: list = []
    runner.engine.events.subscribe(Event, events.append)
    runner.run()
    return events


def test_stream_has_no_orphan_chip_events(captured):
    tracker = ChipTracker()
    for event in captured:
        tracker.apply(event)
    assert tracker.orphans == [], (
        f"{len(tracker.orphans)} events referenced chips the stream never "
        f"placed; first: {tracker.orphans[0]}"
    )


def test_come_bets_travel(captured):
    moves = [e for e in captured if isinstance(e, BetMoved)]
    come_moves = [e for e in moves if e.bet_type in ("Come", "Don't Come")]
    assert come_moves, "no Come/Don't Come travel in 20 seeded shooters"
    assert all(e.number in (4, 5, 6, 8, 9, 10) for e in moves)
    # Every move follows a placement of that bet type by that player.
    placed = {(e.player_name, e.bet_type) for e in captured if isinstance(e, BetPlaced)}
    assert all((e.player_name, e.bet_type) in placed for e in moves)


def test_regression_emits_adjustments(captured):
    adjusted = [e for e in captured if isinstance(e, BetAdjusted)]
    assert any(e.player_name == "Go Big" for e in adjusted), (
        "RegressHalfPress ran 20 shooters without a BetAdjusted"
    )


def test_status_flips_are_published(captured):
    flips = [e for e in captured if isinstance(e, BetStatusChanged)]
    statuses = {e.status for e in flips}
    assert "inactive" in statuses, "no bet ever went off"
    assert "active" in statuses, "no bet ever came back on"


def test_resolved_carries_removal_fact(captured):
    resolved = [e for e in captured if isinstance(e, BetResolved)]
    assert any(e.removed for e in resolved), "no bet ever left the table"
    stay_ups = [e for e in resolved if not e.removed]
    assert stay_ups, "no winner ever stayed up (leave_winning_bets_up=True)"
    assert all(e.status == "won" for e in stay_ups), (
        "only winners may stay on the table"
    )