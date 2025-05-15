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

    # Resolve
    outcome = (3, 4)
    engine.rules_engine.resolve_bet(come_bet, outcome, engine.game_state)
    engine.rules_engine.resolve_bet(come_odds, outcome, engine.game_state)

    assert come_bet.status == "lost"
    assert come_odds.status == "return"

    settled = engine.table.settle_resolved_bets()

    assert come_odds not in engine.table.bets
    assert come_odds in settled
