"""TableRunner's split roll cycle (prepare_next_roll()/roll_and_resolve())
must be equivalent to the old atomic roll_once() — the async
TableSession driver calls them separately (to put a real gap between
bet-placement and dice-throwing for the live felt), while the sync
run() loop and other direct callers still call roll_once(). Both paths
must produce identical engine state."""
from craps.events import DiceRolled, Event, RoundReady
from craps.table_runner import TableRunner

LINEUP = [("Molly", "3-Point Molly"), ("IC", "Iron Cross")]


def _new_runner(seed: int) -> TableRunner:
    runner = TableRunner(
        table_id="split-roll",
        players=LINEUP,
        max_shooters=8,
        dice_seed=seed,
    )
    runner.start_session()
    return runner


def test_split_calls_match_roll_once_bankroll():
    atomic = _new_runner(seed=99)
    split = _new_runner(seed=99)

    for _ in range(60):
        atomic.roll_once()
        split.prepare_next_roll()
        split.roll_and_resolve()

    for atomic_player, split_player in zip(
        atomic.engine.player_lineup.get_active_players_list(),
        split.engine.player_lineup.get_active_players_list(),
    ):
        assert atomic_player.balance == split_player.balance


def test_round_ready_bet_count_matches_accept_bets_return_value():
    runner = _new_runner(seed=7)
    events: list = []
    runner.engine.events.subscribe(RoundReady, events.append)

    total_bets = runner.prepare_next_roll()

    assert len(events) == 1
    assert events[0].bet_count == total_bets


def test_round_ready_precedes_dice_rolled():
    runner = _new_runner(seed=7)
    events: list = []
    runner.engine.events.subscribe(Event, events.append)

    runner.prepare_next_roll()
    runner.roll_and_resolve()

    round_ready_idx = next(i for i, e in enumerate(events) if isinstance(e, RoundReady))
    dice_rolled_idx = next(i for i, e in enumerate(events) if isinstance(e, DiceRolled))
    assert round_ready_idx < dice_rolled_idx
