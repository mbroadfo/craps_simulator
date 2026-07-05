"""Step 0 gate: a recorded session replays to identical stats.

Runs a seeded TableRunner session that records JSONL while also
capturing the live event stream in memory, then verifies two layers:

1. Losslessness — the JSONL, deserialized, equals the captured stream
   event-for-event, with contiguous seq numbers and a constant table_id.
2. Stats reproducibility — feeding the deserialized stream through a
   fresh Statistics + StatsConsumer reproduces the live run's
   event-derived stats exactly: roll counts, ledger totals, per-roll
   bankroll and at-risk histories, shooter results, final bankrolls.

Out of scope by design: seven_out_rolls and point_number_rolls receive
direct writes from GameState in the live run (a Phase 1 fidelity quirk),
and finalize_session's report-side fields (high roller, net_win_loss)
are derived after the stream ends. Neither is part of the losslessness
claim.

Usage: python scripts/verify_replay.py [--seed N] [--shooters N]
                                       [--sessions-dir DIR]
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from craps.consumers import StatsConsumer
from craps.events import Event, EventBus
from craps.player import Player
from craps.session_recorder import load_session
from craps.statistics import Statistics
from craps.table_runner import LineupConfig, TableRunner

DEFAULT_LINEUP: List[Tuple[str, str]] = [
    ("Linus", "Pass-Line"),
    ("Fielder", "Field"),
    ("Crosstopher", "Iron Cross"),
]

#: Statistics attributes populated solely by the event stream.
EVENT_DERIVED_FIELDS = [
    "session_rolls",
    "roll_numbers",
    "total_sevens",
    "max_table_risk",
    "total_amount_bet",
    "total_amount_won",
    "total_amount_lost",
    "player_bankrolls",
    "highest_bankroll",
    "lowest_bankroll",
    "session_highest_bankroll",
    "session_lowest_bankroll",
    "bankroll_history",
    "at_risk_history",
    "shooter_stats",
]

#: player_stats keys the stream drives (finalize_session owns the rest).
EVENT_DERIVED_PLAYER_KEYS = [
    "bets_settled",
    "bets_won",
    "highest_bankroll",
    "lowest_bankroll",
]


def replay_statistics(
    events: List[Event],
    lineup: LineupConfig,
    num_shooters: int,
    table_minimum: int = 10,
) -> Statistics:
    """Re-run stats from a deserialized event stream, engine-free."""
    stand_ins = [Player(name=n, strategy_name=s) for n, s in lineup]
    stats = Statistics(
        table_minimum=table_minimum,
        num_shooters=num_shooters,
        num_players=len(stand_ins),
    )
    stats.initialize_player_stats(stand_ins)
    bus = EventBus()
    StatsConsumer(stats, lambda: stand_ins).subscribe(bus)
    for event in events:
        bus.publish(event)
    return stats


def verify(
    seed: int = 4242,
    num_shooters: int = 10,
    lineup: Optional[LineupConfig] = None,
    sessions_dir: str = "sessions",
) -> Tuple[Statistics, Statistics]:
    """Run live, replay from JSONL, assert parity. Returns both stats."""
    if lineup is None:
        lineup = DEFAULT_LINEUP

    runner = TableRunner(
        table_id="verify",
        players=lineup,
        max_shooters=num_shooters,
        dice_seed=seed,
        record=True,
        sessions_dir=sessions_dir,
    )
    captured: List[Event] = []
    runner.engine.events.subscribe(Event, captured.append)
    live = runner.run()

    assert runner.recorder is not None
    recorded = list(load_session(runner.recorder.path))

    # Layer 1: losslessness of the JSONL stream.
    assert len(recorded) == len(captured), (
        f"event count: recorded {len(recorded)} != live {len(captured)}"
    )
    for i, ((seq, table_id, event), live_event) in enumerate(zip(recorded, captured)):
        assert seq == i, f"seq gap at line {i}: got {seq}"
        assert table_id == "verify", f"table_id mismatch at seq {i}: {table_id!r}"
        assert event == live_event, (
            f"event mismatch at seq {i}:\n  recorded: {event}\n  live:     {live_event}"
        )

    # Layer 2: stats re-run from the recorded stream match the live run.
    replayed = replay_statistics(
        [event for _, _, event in recorded], lineup, num_shooters
    )
    for field in EVENT_DERIVED_FIELDS:
        live_value = getattr(live, field)
        replay_value = getattr(replayed, field)
        assert live_value == replay_value, (
            f"stats.{field}:\n  live:   {live_value}\n  replay: {replay_value}"
        )
    for name, _ in lineup:
        for key in EVENT_DERIVED_PLAYER_KEYS:
            live_value = live.player_stats[name][key]
            replay_value = replayed.player_stats[name][key]
            assert live_value == replay_value, (
                f"player_stats[{name}][{key}]: live {live_value} != replay {replay_value}"
            )
        # Cross-check: the stream's last bankroll IS the final bankroll.
        assert live.player_stats[name]["final_bankroll"] == replayed.bankroll_history[name][-1], (
            f"{name}: final bankroll {live.player_stats[name]['final_bankroll']} != "
            f"last replayed bankroll {replayed.bankroll_history[name][-1]}"
        )

    return live, replayed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Step 0 gate: a recorded session replays to identical stats."
    )
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--shooters", type=int, default=10)
    parser.add_argument("--sessions-dir", default="sessions")
    args = parser.parse_args()

    live, replayed = verify(
        seed=args.seed, num_shooters=args.shooters, sessions_dir=args.sessions_dir
    )
    finals: Dict[str, int] = {
        name: history[-1] for name, history in replayed.bankroll_history.items()
    }
    # ASCII only: Windows consoles default to cp1252.
    print(
        f"OK - replay verified: {live.session_rolls} rolls, "
        f"{len(finals)} players, seed {args.seed}"
    )
    print(f"   Final bankrolls (live == replay): {finals}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
