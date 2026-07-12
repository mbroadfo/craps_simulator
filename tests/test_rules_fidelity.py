"""Casino-rules fidelity (post-Hard-Rock audit, Mike-approved 2026-07-05):

1. Buy/Lay pay true odds minus a 5% commission — on the win by default
   (vig_on_win=True, the Hard Rock model), or charged non-refundable at
   placement when vig_on_win=False.
2. Field 2/12 payouts honor the HouseRules configuration (double vs
   triple) instead of the static table.
3. Any Craps exists: one-roll, wins 7:1 on 2/3/12, gated by
   prop_bets_enabled. (No C&E — Any Craps + the 11 covers it.)
4. Buy is offered on 4/5/9/10 only.
5. The unplayable Horn / Horn High / World stubs are gone.
"""
import pytest

from craps.game_state import GameState
from craps.house_rules import HouseRules
from craps.lineup import PlayerLineup
from craps.play_by_play import PlayByPlay
from craps.player import Player
from craps.rules_engine import RulesEngine
from craps.statistics import Statistics
from craps.table import Table


def make_table(rules_config=None):
    house_rules = HouseRules(rules_config or {})
    play_by_play = PlayByPlay()
    rules_engine = RulesEngine()
    lineup = PlayerLineup(house_rules, None, play_by_play, rules_engine)
    table = Table(house_rules, play_by_play, rules_engine, lineup)
    stats = Statistics(table_minimum=house_rules.table_minimum, num_shooters=1, num_players=1)
    game_state = GameState(stats, play_by_play)
    table.set_game_state(game_state)
    return table, game_state


def roll(table, game_state, dice):
    table.check_bets(dice, game_state)
    return table.settle_resolved_bets()


class TestBuyLayCommission:
    def test_buy_pays_true_odds_minus_vig_on_win(self):
        table, game_state = make_table()
        player = Player("Buyer", initial_balance=1000)
        bet = RulesEngine.create_bet("Buy", 20, player, number=4)
        assert table.place_bet(bet, "point")
        assert player.balance == 1000, "no commission at placement when vig is on win"

        game_state.point = 6
        settled = roll(table, game_state, (2, 2))

        assert bet in settled and bet.status == "won"
        # true odds 2:1 on $20 = $40, minus 5% of $20 = $1
        assert bet.resolved_payout == 39
        assert player.balance == 1039

    def test_lay_vig_is_five_percent_of_potential_win(self):
        table, game_state = make_table()
        player = Player("Layla", initial_balance=1000)
        bet = RulesEngine.create_bet("Lay", 40, player, number=10)
        assert table.place_bet(bet, "point")

        game_state.point = 6
        settled = roll(table, game_state, (3, 4))  # seven: Lay wins

        assert bet in settled and bet.status == "won"
        # lay 40 against the 10 wins 40 * 1/2 = $20, minus 5% of $20 = $1
        assert bet.resolved_payout == 19
        assert player.balance == 1019

    def test_upfront_vig_charged_at_placement(self):
        table, game_state = make_table({"vig_on_win": False})
        player = Player("Buyer", initial_balance=1000)
        bet = RulesEngine.create_bet("Buy", 20, player, number=4)
        assert table.place_bet(bet, "point")
        assert player.balance == 999, "commission due when the bet goes up"

        game_state.point = 6
        roll(table, game_state, (2, 2))
        assert bet.resolved_payout == 40, "upfront tables pay full true odds"
        assert player.balance == 999 + 40

    def test_place_bets_carry_no_commission(self):
        table, game_state = make_table()
        player = Player("Placer", initial_balance=1000)
        bet = RulesEngine.create_bet("Place", 12, player, number=6)
        assert table.place_bet(bet, "point")

        game_state.point = 4
        roll(table, game_state, (3, 3))
        assert bet.resolved_payout == 14  # 7:6, untouched


def field_payout(rules_config, dice):
    """One field bet, one roll, fresh table (winners stay up otherwise)."""
    table, game_state = make_table(rules_config)
    player = Player("Fielder", initial_balance=1000)
    bet = RulesEngine.create_bet("Field", 10, player)
    assert table.place_bet(bet, "come-out")
    roll(table, game_state, dice)
    assert bet.status == "won"
    return bet.resolved_payout


class TestFieldConfiguration:
    def test_configured_triple_2_double_12(self):
        config = {"field_bet_payout_2": 3, "field_bet_payout_12": 2}
        assert field_payout(config, (1, 1)) == 30, "configured triple on the 2"
        assert field_payout(config, (6, 6)) == 20, "configured double on the 12"

    def test_default_config_is_double_2_triple_12(self):
        assert field_payout(None, (1, 1)) == 20
        assert field_payout(None, (6, 6)) == 30

    def test_legacy_ratio_pair_config_still_accepted(self):
        rules = HouseRules({"field_bet_payout_2": (2, 1), "field_bet_payout_12": (3, 1)})
        assert rules.field_bet_payout_2 == 2
        assert rules.field_bet_payout_12 == 3

    def test_ordinary_field_numbers_unaffected(self):
        table, game_state = make_table({"field_bet_payout_2": 3})
        player = Player("Fielder", initial_balance=1000)
        bet = RulesEngine.create_bet("Field", 10, player)
        table.place_bet(bet, "come-out")
        roll(table, game_state, (5, 6))
        assert bet.resolved_payout == 10  # 11 pays even money


class TestAnyCraps:
    @pytest.mark.parametrize("dice", [(1, 1), (1, 2), (6, 6)], ids=["2", "3", "12"])
    def test_wins_seven_to_one_on_craps(self, dice):
        table, game_state = make_table()
        player = Player("Crapper", initial_balance=1000)
        bet = RulesEngine.create_bet("Any Craps", 10, player)
        assert table.place_bet(bet, "come-out")

        settled = roll(table, game_state, dice)
        assert bet in settled and bet.status == "won"
        assert bet.resolved_payout == 70

    def test_loses_on_any_other_roll(self, ):
        table, game_state = make_table()
        player = Player("Crapper", initial_balance=1000)
        bet = RulesEngine.create_bet("Any Craps", 10, player)
        table.place_bet(bet, "come-out")

        settled = roll(table, game_state, (3, 4))
        assert bet in settled and bet.status == "lost"
        assert player.balance == 990

    def test_gated_by_prop_bets_flag(self):
        table, _ = make_table({"prop_bets_enabled": False})
        player = Player("Crapper", initial_balance=1000)
        bet = RulesEngine.create_bet("Any Craps", 10, player)
        valid, message = table.validate_bet(bet, "come-out")
        assert valid is False
        assert message is not None and "does not offer" in message

    def test_takes_no_number(self):
        player = Player("Crapper", initial_balance=1000)
        with pytest.raises(ValueError):
            RulesEngine.create_bet("Any Craps", 10, player, number=2)


class TestBuyNumbers:
    @pytest.mark.parametrize("number", [6, 8])
    def test_buy_6_and_8_rejected(self, number):
        player = Player("Buyer", initial_balance=1000)
        with pytest.raises(ValueError):
            RulesEngine.create_bet("Buy", 20, player, number=number)

    @pytest.mark.parametrize("number", [4, 5, 9, 10])
    def test_buy_outside_numbers_allowed(self, number):
        player = Player("Buyer", initial_balance=1000)
        bet = RulesEngine.create_bet("Buy", 20, player, number=number)
        assert bet.vig is True


class TestCombosRestored:
    """Horn and World are real bets again (felt redline, 2026-07-05);
    Horn High stays gone."""

    def test_horn_high_stays_gone(self):
        with pytest.raises(ValueError, match="Unknown bet type"):
            RulesEngine.get_bet_rules("Horn High")


class TestHornAndWorld:
    @pytest.mark.parametrize("dice,expected", [
        ((1, 1), 27),  # 2: the 30:1 quarter wins, three quarters lose
        ((6, 6), 27),  # 12
        ((1, 2), 12),  # 3: the 15:1 quarter wins
        ((5, 6), 12),  # 11
    ])
    def test_horn_pays_by_rolled_total(self, dice, expected):
        table, game_state = make_table()
        player = Player("Horner", initial_balance=1000)
        bet = RulesEngine.create_bet("Horn", 4, player)
        assert table.place_bet(bet, "come-out")
        settled = roll(table, game_state, dice)
        assert bet in settled and bet.status == "won"
        assert bet.resolved_payout == expected
        assert player.balance == 1000 + expected

    def test_horn_loses_any_other_total(self):
        table, game_state = make_table()
        player = Player("Horner", initial_balance=1000)
        bet = RulesEngine.create_bet("Horn", 4, player)
        assert table.place_bet(bet, "come-out")
        roll(table, game_state, (3, 3))
        assert bet.status == "lost"
        assert player.balance == 996

    def test_horn_bet_in_four_dollar_units(self):
        table, _ = make_table()
        player = Player("Horner", initial_balance=1000)
        bet = RulesEngine.create_bet("Horn", 10, player)
        valid, message = table.validate_bet(bet, "come-out")
        assert valid is False
        assert message is not None and "units of $4" in message

    @pytest.mark.parametrize("dice,expected", [
        ((1, 1), 26),  # 2 per $5: 30:1 fifth minus four losing units
        ((6, 6), 26),  # 12
        ((2, 1), 11),  # 3
        ((5, 6), 11),  # 11
    ])
    def test_world_pays_by_rolled_total(self, dice, expected):
        table, game_state = make_table()
        player = Player("Worldly", initial_balance=1000)
        bet = RulesEngine.create_bet("World", 5, player)
        assert table.place_bet(bet, "come-out")
        settled = roll(table, game_state, dice)
        assert bet in settled and bet.status == "won"
        assert bet.resolved_payout == expected

    def test_world_pushes_on_seven(self):
        table, game_state = make_table()
        player = Player("Worldly", initial_balance=1000)
        bet = RulesEngine.create_bet("World", 5, player)
        assert table.place_bet(bet, "come-out")
        settled = roll(table, game_state, (3, 4))
        assert bet in settled and bet.status == "return"
        assert not table.has_bet(bet), "pushed World comes down"
        assert player.balance == 1000, "push moves no money"

    def test_world_bet_in_five_dollar_units(self):
        table, _ = make_table()
        player = Player("Worldly", initial_balance=1000)
        bet = RulesEngine.create_bet("World", 8, player)
        valid, message = table.validate_bet(bet, "come-out")
        assert valid is False
        assert message is not None and "units of $5" in message

    @pytest.mark.parametrize("bet_type,unit", [("Horn", 4), ("World", 5)])
    def test_takes_no_number(self, bet_type, unit):
        player = Player("Propper", initial_balance=1000)
        with pytest.raises(ValueError):
            RulesEngine.create_bet(bet_type, unit, player, number=2)
