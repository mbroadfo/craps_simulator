from typing import List, Optional, Tuple, TYPE_CHECKING
from craps.bet import Bet
from craps.play_by_play import PlayByPlay
from craps.house_rules import HouseRules
from craps.rules_engine import RulesEngine
from craps.lineup import PlayerLineup

if TYPE_CHECKING:
    from craps.player import Player
    
class Table:
    def __init__(self, house_rules: HouseRules, play_by_play: PlayByPlay, rules_engine: RulesEngine, player_lineup: PlayerLineup) -> None:
        """
        Initialize the table.

        :param house_rules: The HouseRules object for payout rules and limits.
        :param play_by_play: The PlayByPlay instance for logging.
        :param rules_engine: The RulesEngine instance for resolving bets.
        """
        self.house_rules = house_rules
        self.play_by_play = play_by_play
        self.rules_engine = rules_engine  # Use the passed RulesEngine
        self.player_lineup = player_lineup
        self.bets: List[Bet] = []  # All bets on the table
        self.unit = self.house_rules.table_minimum // 5  # Unit for Place/Buy bets

    def get_rules_engine(self) -> RulesEngine:
            """Expose RulesEngine for other classes to query."""
            return self.rules_engine
    
    def has_bet(self, bet: Bet) -> bool:
        """
        Check if a specific bet is on the table.

        :param bet: The bet to check for.
        :return: True if the bet is on the table, False otherwise.
        """
        return bet in self.bets

    def reactivate_inactive_bets(self) -> None:
        """
        Reactivate inactive Place bets when the point is set.
        """
        reactivated_bets = []
        for bet in self.bets:
            if bet.bet_type.startswith("Place") and bet.status == "inactive":
                bet.status = "active"
                reactivated_bets.append(f"{bet.owner.name}'s {bet.bet_type}")

        if reactivated_bets:
            message = f"{', '.join(reactivated_bets)} are now ON."
            self.play_by_play.write(message)

    def place_bet(self, bet: Bet, phase: str) -> bool:
        """
        Place a bet on the table after validating it.

        :param bet: The bet to place.
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet was placed successfully, False otherwise.
        """
        # ✅ Fetch player's preferred bet amount
        bet_amount = self.player_lineup.get_bet_amount(bet.owner)

        if bet.amount != bet_amount:
            message = f"  🔄 Adjusting {bet.owner.name}'s bet from ${bet.amount} to ${bet_amount} (preferred setting)."
            self.play_by_play.write(message)
            bet.amount = bet_amount  # ✅ Apply new amount

        # Validate the bet before placing it
        if not bet.validate_bet(phase, self.house_rules.table_minimum, self.house_rules.table_maximum):
            message = f"  ❌ Invalid bet: {bet}"
            self.play_by_play.write(message)
            return False

        # Place the bet on the table
        self.bets.append(bet)
        return True

    def check_bets(self, dice_outcome: Tuple[int, int], phase: str, point: Optional[int]) -> None:
        """
        Check and resolve all bets on the table based on the dice outcome, phase, and point.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param phase: The current game phase ("come-out" or "point").
        :param point: The current point number (if in point phase).
        """
        for bet in self.bets:
            bet.resolve(self.rules_engine, dice_outcome, phase, point)

    def clear_resolved_bets(self) -> List[Bet]:
        """
        Remove resolved bets from the table and update player bankrolls accordingly.
        """
        resolved_bets = []
        for bet in self.bets:
            if (bet.is_contract_bet and bet.status in ["won", "lost"]) or \
            (not bet.is_contract_bet and bet.status == "lost"):
                resolved_bets.append(bet)

        # Process bankroll updates for each resolved bet
        for bet in resolved_bets:
            if bet.status == "won":
                bet.owner.win_bet(bet, self.play_by_play)
            elif bet.status == "lost":
                bet.owner.lose_bet(bet, self.play_by_play)

        # Remove resolved bets from active table bets
        self.bets = [bet for bet in self.bets if bet not in resolved_bets]
        return resolved_bets
    
    def get_active_players(self) -> List["Player"]:
        """Retrieve all active players at the table."""
        return self.player_lineup.get_active_players_list()

    def notify_players_of_point_hit(self) -> None:
        """
        Notifies each player that the point was hit and asks if they want their Come/Place/Lay Odds working on the next come-out roll.
        """
        for player in self.player_lineup.get_active_players_list():
            if player.has_odds_bets(self):
                should_work = self.player_lineup.should_odds_be_working(player)
                player.update_come_odds_status(self, should_work)
