from typing import Tuple, List, Any, Dict
from craps.lineup import PlayerLineup
from craps.rules_engine import RulesEngine
from craps.play_by_play import PlayByPlay

class SetupPlayers:
    def __init__(self, house_rules: Any, table: Any, active_players_config: Dict[str, bool], play_by_play: PlayByPlay, rules_engine: RulesEngine) -> None:
        """
        Initialize player setup.

        :param house_rules: The HouseRules object for table limits and payouts.
        :param table: The Table object for placing bets.
        :param active_players_config: A dictionary specifying which players are active.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        :param rules_engine: The RulesEngine instance to use for bet creation.
        """
        self.house_rules = house_rules
        self.table = table
        self.active_players_config = active_players_config
        self.play_by_play = play_by_play
        self.rules_engine = rules_engine

    def setup(self) -> Tuple[List[Any], List[str]]:
        """
        Set up the players and their strategies.

        :return: A tuple of (strategies, player_names).
        """
        player_lineup = PlayerLineup(self.house_rules, self.table, self.play_by_play, self.rules_engine)
        strategies, player_names = player_lineup.get_active_players(self.active_players_config)
        return strategies, player_names
