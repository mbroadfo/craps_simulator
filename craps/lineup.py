from typing import Any, Callable, Dict, Optional, List, TYPE_CHECKING

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
        # strategy_name values preserve v1 report labels exactly — including
        # the v1 Molly/Dolly label swap (flagged in Step 4b, kept for output
        # fidelity until a deliberate fix is approved).
        self.all_strategies: Dict[str, Callable[[], V2StrategyAdapter]] = {
            "Pass-Line": lambda: V2StrategyAdapter(
                PassLineV2(bet_amount=tm), strategy_name="PassLine"),
            "Pass-Line w/ Odds": lambda: V2StrategyAdapter(
                PassLineOddsV2(odds_multiple="1x"), strategy_name="PassOdds"),
            "Field": lambda: V2StrategyAdapter(
                FieldV2(min_bet=tm), strategy_name="Field"),
            "Iron Cross": lambda: V2StrategyAdapter(
                IronCrossV2(min_bet=tm, play_pass_line=True, odds_type="3x-4x-5x"),
                strategy_name="IronCross"),
            "3-Point Molly": lambda: V2StrategyAdapter(
                ThreePointMollyV2(bet_amount=tm, odds_type="3x-4x-5x"),
                strategy_name="ThreePointDolly"),
            "3-Point Dolly": lambda: V2StrategyAdapter(
                ThreePointDollyV2(bet_amount=tm, odds_type="3x-4x-5x"),
                strategy_name="ThreePointMolly"),
            "Inside": lambda: V2StrategyAdapter(
                PlaceV2("inside"), strategy_name="Place"),
            "Across": lambda: V2StrategyAdapter(
                PlaceV2("across"), strategy_name="Place"),
            "Place 68": lambda: V2StrategyAdapter(
                PlaceV2([6, 8]), strategy_name="Place"),
            "Double Hop": lambda: V2StrategyAdapter(
                DoubleHopV2(hop_target=(3, 3), base_bet=1), strategy_name="DoubleHop"),
            "Three-Two-One": lambda: V2StrategyAdapter(
                ThreeTwoOneV2(min_bet=tm, odds_type="1x"), strategy_name="ThreeTwoOne"),
            "RegressHalfPress": lambda: V2StrategyAdapter(
                RegressPressV2(high_unit=10, low_unit=3, regression_factor=2, regress_units=5),
                strategy_name="RegressThenPress"),
            "Lay Outside": lambda: V2StrategyAdapter(
                LayV2("Outside"), strategy_name="Lay"),
            "HardwayHighway": lambda: V2StrategyAdapter(
                HardwayHighwayV2(), strategy_name="Hardways"),
            "AllTallSmall": lambda: V2StrategyAdapter(
                AllTallSmallV2(ats_type="AllTallSmall", bet_amount=15),
                strategy_name="AllTallSmall"),
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
                player.betting_strategy = self.all_strategies[player.strategy_name]()
                self.add_player(player)
            else:
                raise ValueError(f"No strategy found for player '{player.name}'")
