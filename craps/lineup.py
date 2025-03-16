from typing import Dict, Optional, List, Any, TYPE_CHECKING
from craps.strategies.pass_line_strategy import PassLineStrategy
from craps.strategies.place_strategy import PlaceBetStrategy
from craps.strategies.field_strategy import FieldBetStrategy
from craps.strategies.iron_cross_strategy import IronCrossStrategy
from craps.strategies.three_point_molly_strategy import ThreePointMollyStrategy
from craps.rules_engine import RulesEngine

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

        # ✅ Store actual Player instances and their configurations
        self.players: Dict["Player", Dict[str, Any]] = {}

        # Define all supported strategies
        self.all_strategies: Dict[str, Any] = {
            "Pass-Line": PassLineStrategy(bet_amount=self.house_rules.table_minimum, table=self.table),
            "Pass-Line w/ Odds": PassLineStrategy(
                bet_amount=self.house_rules.table_minimum,
                table=self.table,
                odds_type="3x-4x-5x"
            ),
            "Place Inside": PlaceBetStrategy(table=self.table, numbers_or_strategy="inside", rules_engine=self.rules_engine),
            "Place Across": PlaceBetStrategy(table=self.table, numbers_or_strategy="across", rules_engine=self.rules_engine),
            "Field": FieldBetStrategy(min_bet=self.house_rules.table_minimum),
            "Iron Cross": IronCrossStrategy(
                table=self.table, min_bet=self.house_rules.table_minimum, play_by_play=self.play_by_play, rules_engine=self.rules_engine
            ),
            "3-Point Molly": ThreePointMollyStrategy(
                table=self.table, min_bet=self.house_rules.table_minimum, odds_type="3x-4x-5x", rules_engine=self.rules_engine
            )
        }

    def add_player(self, player: "Player", bet_amount: Optional[int] = None, odds_working_on_come_out: bool = False) -> None:
        """
        Adds a Player instance to the lineup with custom bet settings.

        :param player: The Player instance to add.
        :param bet_amount: Custom bet amount (default: None = table minimum).
        :param odds_working_on_come_out: Whether Come/Place/Lay Odds stay ON during come-out.
        """
        self.players[player] = {
            "bet_amount": bet_amount or self.house_rules.table_minimum,  # Default to table min
            "odds_working_on_come_out": odds_working_on_come_out
        }

    def get_active_players_list(self) -> List["Player"]:
        """Retrieve a list of active player objects."""
        return list(self.players.keys())  # ✅ Return actual Player instances
    
    def get_strategy_for_player(self, player: "Player") -> Optional[Any]:
        """Retrieve the strategy for a given player."""
        return player.betting_strategy if player in self.players else None
    
    def get_bet_amount(self, player: "Player") -> int:
        """Retrieve the bet amount for a given player."""
        return self.players.get(player, {}).get("bet_amount", self.house_rules.table_minimum)

    def should_odds_be_working(self, player: "Player") -> bool:
        """Check if this player's odds bets should stay ON during the come-out roll."""
        return self.players.get(player, {}).get("odds_working_on_come_out", False)
