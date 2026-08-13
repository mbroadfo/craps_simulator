import pytest
from craps.craps_engine import CrapsEngine
from craps.player import Player
from craps.rules_engine import RulesEngine
from craps.bet import Bet

def setup_basic_engine():
    engine = CrapsEngine(quiet_mode=True)
    engine.setup_session(num_shooters=1, num_players=0)
    player = Player("Molly", strategy_name="3-Point Molly")
    engine.player_lineup.assign_strategies([player])
    engine.stats.initialize_player_stats([player])
    engine.player_lineup.players = [player]
    engine.assign_next_shooter()
    engine.lock_session()
    return engine, player

def test_come_bet_resolves_before_new_movement():
    engine, player = setup_basic_engine()

    # Create a come bet and simulate it's already moved to 6
    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 6  # Manually assign number to simulate post-move
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    # Attach odds to Come 6
    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "active"
    engine.table.bets.append(come_odds)

    # New Come bet (not yet moved)
    pending_come = RulesEngine.create_bet("Come", 10, player)
    pending_come.status = "active"
    engine.table.bets.append(pending_come)

    # Resolve bet statuses only
    outcome = (1, 5)  # total = 6
    engine.table.check_bets(outcome, engine.game_state)

    assert come_bet.status == "won"
    assert come_odds.status == "won"
    assert pending_come.status == "move 6"

    settled = engine.table.settle_resolved_bets()

    assert come_bet not in engine.table.bets
    assert come_odds not in engine.table.bets
    assert pending_come in engine.table.bets
    assert pending_come.status == "active"
    assert pending_come.number == 6


def test_come_odds_removed_on_come_out_7():
    engine, player = setup_basic_engine()

    # Create Come bet, simulate already moved to 9
    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 9
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    # Attach odds
    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "active"
    engine.table.bets.append(come_odds)

    # Simulate come-out
    engine.game_state._point = None
    engine.game_state._puck_on = False
    assert engine.game_state.phase == "come-out"

    balance_before = player.balance

    # Resolve
    outcome = (3, 4)
    engine.rules_engine.resolve_bet(come_bet, outcome, engine.game_state)
    engine.rules_engine.resolve_bet(come_odds, outcome, engine.game_state)

    assert come_bet.status == "lost"
    assert come_odds.status == "return"

    settled = engine.table.settle_resolved_bets()

    assert come_odds not in engine.table.bets
    assert come_odds in settled
    # Regression: a Come Odds bet returned on a come-out loss must not
    # be charged as a loss — place_bet() never deducted its amount up
    # front, so "return" means no bankroll change at all. table.py used
    # to fold "return" into the same branch as "lost" and call
    # lose_bet() unconditionally, silently charging a bet that was
    # supposed to be refunded.
    assert player.balance == balance_before - come_bet.amount


def test_come_odds_stays_placed_when_parent_still_active():
    """Regression test for the reported bug: odds bets used to be swept
    (removed) every roll their parent didn't itself resolve, so the
    strategy re-placed a fresh one next roll — real casinos leave odds
    bets placed continuously instead. settle_resolved_bets() must now
    leave a still-active parent-linked bet exactly where it is: no
    removal, no status mutation, no BetResolved event.
    """
    engine, player = setup_basic_engine()

    # Come bet already moved to 6, still active — this roll won't
    # resolve it (not 6, not 7).
    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 6
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "active"
    engine.table.bets.append(come_odds)

    outcome = (4, 4)  # total = 8 — doesn't touch a Come bet sitting on 6
    engine.table.check_bets(outcome, engine.game_state)

    assert come_bet.status == "active"
    assert come_odds.status == "active"

    settled = engine.table.settle_resolved_bets()

    assert come_bet in engine.table.bets
    assert come_odds in engine.table.bets       # no longer swept
    assert come_odds.status == "active"         # untouched
    assert come_odds not in settled             # not reported at all


def test_come_odds_persists_across_several_non_resolving_rolls():
    """Regression guard against ever reintroducing the sweep: a
    traveled Come bet and its odds must survive many consecutive rolls
    that touch neither of them, staying on the table the whole time."""
    engine, player = setup_basic_engine()

    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 6
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "active"
    engine.table.bets.append(come_odds)

    for _ in range(10):
        outcome = (2, 2)  # total = 4 — irrelevant to a Come bet on 6
        engine.table.check_bets(outcome, engine.game_state)
        engine.table.settle_resolved_bets()
        assert come_bet in engine.table.bets
        assert come_odds in engine.table.bets
        assert come_odds.status == "active"
        assert come_odds.amount == 50


def test_inactive_come_odds_returned_without_payout_when_parent_wins():
    """If Come Odds are toggled off (status="inactive", e.g. during
    come-out per house_rules.come_odds_working_on_come_out), and the
    parent Come bet's number then hits, resolve_bet() never touches the
    inactive odds bet's status (it early-returns for any non-"active"
    bet) — it must be removed and refunded, not paid, when the parent
    resolves.
    """
    engine, player = setup_basic_engine()

    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 6
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "inactive"  # toggled off
    engine.table.bets.append(come_odds)

    balance_before = player.balance

    outcome = (3, 3)  # total = 6 — the Come bet's number hits
    engine.table.check_bets(outcome, engine.game_state)

    assert come_bet.status == "won"
    assert come_odds.status == "inactive"  # resolve_bet() left it alone

    settled = engine.table.settle_resolved_bets()

    assert come_odds not in engine.table.bets
    assert come_odds in settled
    # No payout for the inactive odds bet, but the Come bet itself
    # still won normally.
    assert player.balance == balance_before + come_bet.payout()
    # Reported honestly as a refund, not silently left "inactive" —
    # the frontend needs one recognizable status to render a distinct
    # "Returned" toast/feed line instead of a loss.
    assert come_odds.status == "return"


def test_inactive_come_odds_returned_without_charge_when_parent_loses():
    """Regression test for a real reported bug: a come-out 7 sevens out
    a traveled Come bet while its Come Odds are toggled off (the normal
    state during come-out, per refresh_bet_statuses()) — the odds must
    be refunded, not charged, and reported as "return" so the felt
    doesn't render a loss toast for money that was never taken.
    """
    engine, player = setup_basic_engine()

    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 6
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "inactive"  # toggled off, as it is by default during come-out
    engine.table.bets.append(come_odds)

    balance_before = player.balance

    outcome = (3, 4)  # total = 7 — sevens out the traveled Come bet
    engine.table.check_bets(outcome, engine.game_state)

    assert come_bet.status == "lost"
    assert come_odds.status == "inactive"  # resolve_bet() left it alone (still inactive)

    settled = engine.table.settle_resolved_bets()

    assert come_odds not in engine.table.bets
    assert come_odds in settled
    assert come_odds.status == "return"
    # Only the Come bet's own $10 is charged — the odds are refunded.
    assert player.balance == balance_before - come_bet.amount


def test_come_odds_toggle_flips_with_phase_via_refresh_bet_statuses():
    """The working/not-working toggle itself: refresh_bet_statuses()
    (craps_engine.py) must flip a traveled Come bet's odds inactive
    once the main game returns to come-out, and back to active once a
    new point is established — the same phase-driven pattern already
    used for Place/Buy/Lay bets.
    """
    engine, player = setup_basic_engine()
    assert engine.house_rules is not None
    assert not engine.house_rules.come_odds_working_on_come_out

    come_bet = RulesEngine.create_bet("Come", 10, player)
    come_bet.number = 6
    come_bet.status = "active"
    engine.table.bets.append(come_bet)

    come_odds = RulesEngine.create_bet("Come Odds", 50, player, parent_bet=come_bet)
    come_odds.status = "active"
    engine.table.bets.append(come_odds)

    # Main point is on: odds stay active.
    engine.game_state._point = 8
    engine.game_state._puck_on = True
    engine.refresh_bet_statuses()
    assert come_odds.status == "active"

    # Point resolves, main game returns to come-out: odds go off.
    engine.game_state._point = None
    engine.game_state._puck_on = False
    engine.refresh_bet_statuses()
    assert come_odds.status == "inactive"

    # A new point is established: odds come back on.
    engine.game_state._point = 5
    engine.game_state._puck_on = True
    engine.refresh_bet_statuses()
    assert come_odds.status == "active"
