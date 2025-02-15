# File: lineup.py
from craps.strategies.pass_line import PassLineStrategy
from craps.strategies.pass_line_odds import PassLineOddsStrategy
from craps.strategies.place_bet import PlaceBetStrategy
from craps.strategies.field_bet import FieldBetStrategy
from craps.strategies.iron_cross import IronCrossStrategy

class PlayerLineup:
    """Class to manage the lineup of players and their strategies."""
    def __init__(self, house_rules, table):
        """
        Initialize the player lineup.
        
        :param house_rules: The HouseRules object for table limits and payouts.
        :param table: The Table object for placing bets.
        """
        self.house_rules = house_rules
        self.table = table

        # Define all possible strategies and their names
        self.all_strategies = {
            "Pass-Line": PassLineStrategy(min_bet=self.house_rules.table_minimum),
            "Pass-Line w/ Odds": PassLineOddsStrategy(table=self.table, odds_multiple=1),
            "$44 Inside": PlaceBetStrategy(table=self.table, numbers_or_strategy="inside"),
            "$54 Across": PlaceBetStrategy(table=self.table, numbers_or_strategy="across"),
            "Field": FieldBetStrategy(min_bet=self.house_rules.table_minimum),
            "Iron Cross": IronCrossStrategy(table=self.table, min_bet=self.house_rules.table_minimum),
        }

    def get_active_players(self, active_players_config):
        """
        Get the list of active strategies and player names based on the configuration.
        
        :param active_players_config: A dictionary specifying which players are active.
        :return: A tuple of (strategies, player_names).
        """
        strategies = [strategy for name, strategy in self.all_strategies.items() if active_players_config.get(name, False)]
        player_names = [name for name, active in active_players_config.items() if active]
        return strategies, player_names