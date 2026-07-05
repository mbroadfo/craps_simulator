"""D6 availability flags: HouseRules declares what the table offers,
Table.validate_bet enforces it (Phase 2, Step 1).

Defaults are open — a config with no flags behaves exactly as before,
which is what keeps every Phase 1 gate green.
"""
import pytest

from craps.house_rules import HouseRules
from craps.lineup import PlayerLineup
from craps.play_by_play import PlayByPlay
from craps.player import Player
from craps.rules_engine import RulesEngine
from craps.table import Table

BARE_BONES = {
    "ats_enabled": False,
    "hardways_enabled": False,
    "hop_bets_enabled": False,
    "prop_bets_enabled": False,
}

FLAG_GATED_BETS = [
    ("All", 15, None, "come-out"),
    ("Tall", 15, None, "come-out"),
    ("Small", 15, None, "come-out"),
    ("Hardways", 10, 8, "point"),
    ("Hop", 1, (3, 3), "point"),
    ("Proposition", 5, 7, "come-out"),
    ("Any Craps", 5, None, "come-out"),
]


def make_table(rules_config):
    house_rules = HouseRules(rules_config)
    play_by_play = PlayByPlay()
    rules_engine = RulesEngine()
    lineup = PlayerLineup(house_rules, None, play_by_play, rules_engine)
    return Table(house_rules, play_by_play, rules_engine, lineup)


def test_defaults_are_open():
    rules = HouseRules({})
    assert rules.ats_enabled is True
    assert rules.hardways_enabled is True
    assert rules.hop_bets_enabled is True
    assert rules.prop_bets_enabled is True


def test_to_dict_round_trips_flags():
    rules = HouseRules(BARE_BONES)
    assert HouseRules(rules.to_dict()).to_dict() == rules.to_dict()
    for flag in BARE_BONES:
        assert rules.to_dict()[flag] is False


@pytest.mark.parametrize("bet_type,amount,number,phase", FLAG_GATED_BETS,
                         ids=[b[0] for b in FLAG_GATED_BETS])
def test_bare_bones_table_refuses_gated_bets(bet_type, amount, number, phase):
    table = make_table(BARE_BONES)
    player = Player("Propper", initial_balance=1000)
    bet = RulesEngine.create_bet(bet_type, amount, player, number=number)

    valid, message = table.validate_bet(bet, phase)
    assert valid is False
    assert message is not None and "does not offer" in message
    assert table.place_bet(bet, phase) is False
    assert bet not in table.bets


@pytest.mark.parametrize("bet_type,amount,number,phase", FLAG_GATED_BETS,
                         ids=[b[0] for b in FLAG_GATED_BETS])
def test_open_table_accepts_gated_bets(bet_type, amount, number, phase):
    table = make_table({})
    player = Player("Propper", initial_balance=1000)
    bet = RulesEngine.create_bet(bet_type, amount, player, number=number)

    valid, message = table.validate_bet(bet, phase)
    assert valid is True, f"open table refused {bet_type}: {message}"


def test_line_bets_unaffected_by_bare_bones():
    table = make_table(BARE_BONES)
    player = Player("Linus", initial_balance=1000)
    bet = RulesEngine.create_bet("Pass Line", 10, player)
    valid, message = table.validate_bet(bet, "come-out")
    assert valid is True, f"Pass Line refused on bare-bones table: {message}"
