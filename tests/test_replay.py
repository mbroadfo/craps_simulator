"""Step 0 gate as a pytest: seeded session → JSONL → identical stats.

Imports the verification logic from scripts/verify_replay.py so the gate
has a single source of truth; CI runs it here, humans run the script.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import verify_replay  # noqa: E402  # pyright: ignore[reportMissingImports] — scripts/ path added above

from craps.session_recorder import load_session  # noqa: E402
from craps.table_runner import TableRunner  # noqa: E402


def test_recorded_session_replays_to_identical_stats(tmp_path):
    live, replayed = verify_replay.verify(
        seed=1234, num_shooters=3, sessions_dir=str(tmp_path)
    )
    assert live.session_rolls > 0
    assert live.session_rolls == replayed.session_rolls


def test_same_seed_records_identical_streams(tmp_path):
    streams = []
    for run in range(2):
        runner = TableRunner(
            table_id="twin",
            players=[("Linus", "Pass-Line")],
            max_shooters=2,
            dice_seed=99,
            record=True,
            sessions_dir=str(tmp_path / f"run{run}"),
        )
        runner.run()
        assert runner.recorder is not None
        streams.append([event for _, _, event in load_session(runner.recorder.path)])
    assert streams[0] == streams[1]


def test_max_rolls_stops_the_runner(tmp_path):
    runner = TableRunner(
        table_id="short",
        players=[("Linus", "Pass-Line")],
        max_shooters=10,
        max_rolls=5,
        dice_seed=7,
        record=True,
        sessions_dir=str(tmp_path),
    )
    stats = runner.run()
    assert stats.session_rolls == 5
    assert runner.recorder is not None
    # Recorder file is closed and readable even without SessionFinalized-
    # triggered close (finalize emits it, but the explicit close also ran).
    events = [event for _, _, event in load_session(runner.recorder.path)]
    assert sum(1 for e in events if type(e).__name__ == "DiceRolled") == 5
