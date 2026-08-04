from typing import Any, Callable, Dict, NamedTuple, Optional, List, TYPE_CHECKING

from craps.rules_engine import RulesEngine
from craps.strategy_contract import V2StrategyAdapter
from craps.strategies.pass_line_v2 import PassLineV2
from craps.strategies.pass_line_odds_v2 import PassLineOddsV2
from craps.strategies.field_v2 import FieldV2
from craps.strategies.iron_cross_v2 import IronCrossV2
from craps.strategies.place_v2 import PlaceV2
from craps.strategies.lay_v2 import LayV2
from craps.strategies.double_hop_v2 import DoubleHopV2
from craps.strategies.hardway_highway_v2 import HardwayHighwayV2
from craps.strategies.all_tall_small_v2 import AllTallSmallV2
from craps.strategies.three_point_v2 import ThreePointMollyV2, ThreePointDollyV2
from craps.strategies.three_two_one_v2 import ThreeTwoOneV2
from craps.strategies.regress_press_v2 import RegressPressV2

if TYPE_CHECKING:
    from craps.player import Player


class StrategyEntry(NamedTuple):
    """A strategy's fresh-adapter factory alongside its casino-vernacular dealer call (Observatory panel bubble, Tier 1)."""
    factory: Callable[[], V2StrategyAdapter]
    dealer_call: str


class PlayerLineup:
    """Class to manage the lineup of players and their strategies."""

    def __init__(self, house_rules: Any, table: Any, play_by_play: Any, rules_engine: RulesEngine) -> None:
        """
        Initialize the player lineup.

        :param house_rules: The HouseRules object for table limits and payouts.
        :param table: The Table object for placing bets.
        :param play_by_play: The PlayByPlay instance for logging game actions.
        :param rules_engine: The RulesEngine instance for bet validation.
        """
        self.house_rules = house_rules
        self.table = table
        self.play_by_play = play_by_play
        self.rules_engine = rules_engine

        # Store actual Player instances
        self.players: List["Player"] = []

        tm = self.house_rules.table_minimum

        # Factories: each player gets a fresh adapter, so per-player memo
        # state never leaks between players sharing a strategy name.
        # dealer_call is a static, per-strategy come-out opening line for
        # the Observatory panel's roster speech bubble (Tier 1 — no
        # dynamic mid-hand narration yet).
        self.all_strategies: Dict[str, StrategyEntry] = {
            "Pass-Line": StrategyEntry(
                factory=lambda: V2StrategyAdapter(PassLineV2(bet_amount=tm), strategy_name="PassLine"),
                dealer_call="$10 on the line"),
            "Pass-Line w/ Odds": StrategyEntry(
                factory=lambda: V2StrategyAdapter(PassLineOddsV2(odds_multiple="1x"), strategy_name="PassOdds"),
                dealer_call="$10 on the line with full odds behind"),
            "Field": StrategyEntry(
                factory=lambda: V2StrategyAdapter(FieldV2(min_bet=tm), strategy_name="Field"),
                dealer_call="$10 on the field every roll"),
            "Iron Cross": StrategyEntry(
                factory=lambda: V2StrategyAdapter(
                    IronCrossV2(min_bet=tm, play_pass_line=True, odds_type="3x-4x-5x"),
                    strategy_name="IronCross"),
                dealer_call="$10 on the line — inside for $34 and the field"),
            "3-Point Molly": StrategyEntry(
                factory=lambda: V2StrategyAdapter(
                    ThreePointMollyV2(bet_amount=tm, odds_type="3x-4x-5x"),
                    strategy_name="ThreePointMolly"),
                dealer_call="$10 on the line, chasing two come bets with odds"),
            "3-Point Dolly": StrategyEntry(
                factory=lambda: V2StrategyAdapter(
                    ThreePointDollyV2(bet_amount=tm, odds_type="3x-4x-5x"),
                    strategy_name="ThreePointDolly"),
                dealer_call="$10 on the don't, laying two don't comes"),
            "Inside": StrategyEntry(
                factory=lambda: V2StrategyAdapter(PlaceV2("inside"), strategy_name="Place"),
                dealer_call="$44 inside — the five, six, eight, and nine"),
            "Across": StrategyEntry(
                factory=lambda: V2StrategyAdapter(PlaceV2("across"), strategy_name="Place"),
                dealer_call="$64 across — every number covered"),
            "Place 68": StrategyEntry(
                factory=lambda: V2StrategyAdapter(PlaceV2([6, 8]), strategy_name="Place"),
                dealer_call="Give me the six and eight for $12 each"),
            "Double Hop": StrategyEntry(
                factory=lambda: V2StrategyAdapter(
                    DoubleHopV2(hop_target=(3, 3), base_bet=1), strategy_name="DoubleHop"),
                dealer_call="Hopping the hard ways — thirty to one"),
            "Three-Two-One": StrategyEntry(
                factory=lambda: V2StrategyAdapter(ThreeTwoOneV2(min_bet=tm, odds_type="1x"), strategy_name="ThreeTwoOne"),
                dealer_call="$10 on the line, pressing three-two-one"),
            "RegressHalfPress": StrategyEntry(
                factory=lambda: V2StrategyAdapter(
                    RegressPressV2(high_unit=10, low_unit=3, regression_factor=2, regress_units=5),
                    strategy_name="RegressThenPress"),
                dealer_call="Regress then press — start high, lock up profit"),
            "Lay Outside": StrategyEntry(
                factory=lambda: V2StrategyAdapter(LayV2("Outside"), strategy_name="Lay"),
                dealer_call="Laying the four and ten — wrong side outside"),
            "HardwayHighway": StrategyEntry(
                factory=lambda: V2StrategyAdapter(HardwayHighwayV2(), strategy_name="Hardways"),
                dealer_call="Hard six, hard eight, hard four, hard ten working"),
            "AllTallSmall": StrategyEntry(
                factory=lambda: V2StrategyAdapter(
                    AllTallSmallV2(ats_type="AllTallSmall", bet_amount=15),
                    strategy_name="AllTallSmall"),
                dealer_call="$15 each on the all, tall, and small"),
        }

    def add_player(self, player: "Player") -> None:
        """Adds a Player instance to the lineup."""
        self.players.append(player)

    def get_active_players_list(self) -> List["Player"]:
        """Retrieve a list of active player objects."""
        return self.players  # ✅ Return actual Player instances

    def get_strategy_for_player(self, player: "Player") -> Optional[Any]:
        """Retrieve the strategy for a given player."""
        return player.betting_strategy if player in self.players else None

    def should_odds_be_working(self, player: "Player") -> bool:
        """
        Determine if the player's strategy wants Come/Place/Lay odds working on a come-out roll.
        """
        strategy = self.get_strategy_for_player(player)
        if strategy and hasattr(strategy, "should_come_odds_be_working"):
            return strategy.should_come_odds_be_working()
        return False

    def get_bet_amount(self, player: "Player") -> int:
        """
        Retrieve the bet amount for a given player.
        Defaults to the house table minimum if not explicitly set.
        """
        strategy = self.get_strategy_for_player(player)
        if strategy and hasattr(strategy, "bet_amount"):
            return strategy.bet_amount
        return self.house_rules.table_minimum

    def assign_strategies(self, players: List["Player"]) -> None:
        """
        Assigns a fresh betting strategy instance to each player by name
        and adds them to the lineup.
        """
        for player in players:
            if player.strategy_name in self.all_strategies:
                player.betting_strategy = self.all_strategies[player.strategy_name].factory()
                self.add_player(player)
            else:
                raise ValueError(f"No strategy found for player '{player.name}'")
