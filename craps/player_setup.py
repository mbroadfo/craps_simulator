# File: .\craps\player_setup.py

from craps.lineup import PlayerLineup

class SetupPlayers:
    def __init__(self, house_rules, table, active_players_config):
        self.house_rules = house_rules
        self.table = table
        self.active_players_config = active_players_config

    def setup(self):
        """Set up the players and their strategies."""
        player_lineup = PlayerLineup(self.house_rules, self.table)
        strategies, player_names = player_lineup.get_active_players(self.active_players_config)
        return strategies, player_names