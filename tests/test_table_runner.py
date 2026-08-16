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


def test_table_is_swept_clean_after_the_final_shooters_seven_out():
    """Regression test for a real reported bug: bets were still visible
    on the felt after the last shooter's 7-out. A winning Place/Buy/Lay
    bet that stays up per leave_winning_bets_up (the default house
    rule) is normal mid-session — the next shooter's rolls eventually
    resolve or re-activate it. But there IS no next shooter after the
    final one, so without an explicit sweep it just lingers on the
    table (and, via its already-published BetResolved, on the felt)
    forever. Mirrors the async TableSession._drive() loop: call
    prepare_next_roll()/roll_and_resolve() directly and stop once
    shooters_done reaches max_shooters.
    """
    runner = TableRunner(
        table_id="sweep-check",
        # "Lay Outside" places Lay bets, which win (not lose) on a
        # 7-out — combined with the default leave_winning_bets_up house
        # rule, that's exactly the case that used to strand chips on
        # the felt after the session ended (confirmed via direct repro
        # before this fix: 2 leftover Lay bets, every seed tried).
        players=[("Layla", "Lay Outside")],
        max_shooters=3,
        dice_seed=11,
    )
    runner.start_session()

    shooters_done = 0
    while shooters_done < runner.max_shooters:
        runner.prepare_next_roll()
        summary = runner.roll_and_resolve()
        if summary.new_shooter_assigned:
            shooters_done += 1

    assert runner.engine.table.bets == []
