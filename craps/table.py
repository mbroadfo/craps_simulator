from typing import List, Optional, Tuple, TYPE_CHECKING, Union
from craps.bet import Bet
from craps.play_by_play import PlayByPlay
from craps.house_rules import HouseRules
from craps.rules_engine import RulesEngine
from craps.lineup import PlayerLineup
from craps.game_state import GameState
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
        self.game_state: Optional[GameState] = None

    def get_rules_engine(self) -> RulesEngine:
        """Expose RulesEngine for other classes to query."""
        return self.rules_engine

    def set_game_state(self, game_state: GameState) -> None:
        self.game_state = game_state

    def has_bet(self, bet: Bet) -> bool:
        """
        Check if a specific bet is on the table.

        :param bet: The bet to check for.
        :return: True if the bet is on the table, False otherwise.
        """
        return bet in self.bets

    def has_existing_bet(self, player: Player, bet_type: str, number: Optional[Union[int, tuple[int, int]]] = None) -> bool:
        """
        Check if the player already has an active bet of the same type and number.

        :param player: The player placing the bet.
        :param bet_type: The type of bet (e.g., "All", "Place").
        :param number: The number associated with the bet (e.g., 6 or (2, 5) for Hop bets).
        :return: True if an active duplicate bet exists.
        """
        for bet in self.bets:
            if (
                bet.owner == player
                and bet.bet_type == bet_type
                and bet.number == number
            ):
                return True
        return False

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

    def place_bet(self, bet: Bet, phase: str, play_by_play: Optional[PlayByPlay]=None) -> bool:
        """
        Place a bet on the table after validating it.

        :param bet: The bet to place.
        :param phase: The current game phase ("come-out" or "point").
        :return: True if the bet was placed successfully, False otherwise.
        """
        # Validate bet
        valid, message = self.rules_engine.validate_bet_phase(bet=bet, phase=phase)
        if valid:
            valid, message = self.validate_bet(bet, phase)

        if not valid:
            if self.play_by_play and message:
                self.play_by_play.write(f"  🚫 {message}")
            return False

        # Place the bet on the table
        bet.resolved_payout = 0  # Reset in case reused
        self.bets.append(bet)
        return True

    def validate_bet(self, bet: Bet, phase: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a bet against table rules including phase, limits, units, duplicates, and bankroll.

        :param bet: The bet to validate.
        :param phase: The current game phase.
        :return: Tuple of (is_valid, message).
        """
        # Phase validation via RulesEngine
        if not self.rules_engine.validate_bet_phase(bet, phase):
            return False, f"{bet.owner.name}'s {bet.bet_type} bet cannot be placed during the {phase} phase."

        # Validate existing bet
        if self.has_existing_bet(bet.owner, bet.bet_type, bet.number):
            message = f"{bet.owner.name} already has an active {bet.bet_type} bet"
            if bet.number is not None:
                message += f" on {bet.number}"
            message += "."
            return False, message

        bets_with_table_minimums = ["Pass", "Don't Pass", "Come", "Don't Come", "Place", "Buy", "Lay"]
        minimum = self.house_rules.table_minimum if bet.bet_type in bets_with_table_minimums else 1
        maximum = self.house_rules.table_maximum

        # Validate table minimum
        if bet.amount < minimum:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet (${bet.amount}) is below table minimum (${minimum})."

        # Validate table maximum
        if bet.amount > maximum:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet (${bet.amount}) exceeds table maximum (${maximum})."

        # Validate bet sizing
        unit = bet.unit or 1
        if bet.amount % unit != 0:
            return False, f"{bet.owner.name}'s {bet.bet_type} bet of ${bet.amount} must be in units of ${unit}."

        # Validate sufficient bankroll
        total_risk = sum(b.amount for b in self.bets if b.owner == bet.owner)
        if bet.amount + total_risk > bet.owner.balance:
            return False, (
                f"{bet.owner.name} cannot afford ${bet.amount} on {bet.bet_type} — "
                f"balance ${bet.owner.balance}, already risking ${total_risk}."
            )
        # ATS validation using GameState
        if bet.bet_type == "All" and self.game_state and self.game_state.all_completed:
            return False, f"{bet.owner.name} cannot remake All bet — already completed this shooter."
        if bet.bet_type == "Tall" and self.game_state and self.game_state.tall_completed:
            return False, f"{bet.owner.name} cannot remake Tall bet — already completed this shooter."
        if bet.bet_type == "Small" and self.game_state and self.game_state.small_completed:
            return False, f"{bet.owner.name} cannot remake Small bet — already completed this shooter."
        
        return True, None

    def check_bets(self, dice_outcome: Tuple[int, int], game_state: GameState) -> List[Bet]:
        """
        Check and resolve all bets on the table based on the dice outcome, phase, and point.
        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :param game_state: The current GameState object.
        :return: List of bets that were resolved (won/lost)
        """
        resolved_bets: List[Bet] = []

        # 🥇 First pass: resolve non-odds bets
        for bet in self.bets:
            if bet.status == "inactive":
                continue
            if bet.bet_type not in ["Pass Line Odds", "Come Odds", "Don't Pass Odds", "Don't Come Odds"]:
                original_number = bet.number
                original_status = bet.status

                bet.resolve(self.rules_engine, dice_outcome, game_state)

                if bet.status != original_status and bet.status in ("won", "lost"):
                    resolved_bets.append(bet)

                if (
                    bet.bet_type in ["Come", "Don't Come"]
                    and original_number is None
                    and bet.number is not None
                    and bet.status == "active"
                ):
                    self.play_by_play.write(f"  ⏫ {bet.owner.name}'s {bet.bet_type} bet moves to the {bet.number}.")
                elif bet.status == "push":
                    self.play_by_play.write(f"  ⏸️ {bet.owner.name}'s {bet.bet_type} bet was barred and did not move.")

        # 🥈 Second pass: resolve odds bets (parent statuses are now reliable)
        for bet in self.bets:
            if bet.status == "inactive":
                continue
            if bet.bet_type in ["Pass Line Odds", "Come Odds", "Don't Pass Odds", "Don't Come Odds"]:
                original_status = bet.status
                bet.resolve(self.rules_engine, dice_outcome, game_state)

                if bet.status != original_status and bet.status in ("won", "lost", "return"):
                    resolved_bets.append(bet)

        return resolved_bets

    def settle_resolved_bets(self) -> List[Bet]:
        """
        Settle resolved bets by paying winners, removing losers, and resetting status.
        - Winning bets are paid and Player bankroll increased by winnings.
        - Losing bets are removed & Player bankroll reduced by bet amount.
        - Contract bets are returned to the player if they win and removed if they lose.
        - Linked odds bets follow the resolution of their parent bet.
        - Whether bets should stay working and/or to leave winning bets up controlled by HOUSE RULES.
        - Winners that remain on the table will keep status='won' temporarily (for stats),
        and are flipped to 'active' afterward by caller.
        """
        settled_bets: List[Bet] = []
        resolved_bet_ids = set()

        for bet in list(self.bets):
            # Skip odds bets — will be handled with their parent
            if bet.parent_bet is not None:
                continue

            # ✅ Handle Lost Bets
            if bet.status == "lost":
                bet.hits = 0
                bet.owner.lose_bet(bet, self.play_by_play)
                self.bets.remove(bet)
                settled_bets.append(bet)
                resolved_bet_ids.add(id(bet))

                # Also settle attached odds bets
                for attached in list(self.bets):
                    if attached.parent_bet == bet:
                        attached.owner.lose_bet(attached, self.play_by_play)
                        self.bets.remove(attached)
                        settled_bets.append(attached)
                        resolved_bet_ids.add(id(attached))

            # ✅ Handle Winning Bets
            elif bet.status == "won":
                bet.hits += 1
                bet.owner.win_bet(bet, self.play_by_play)
                settled_bets.append(bet)
                resolved_bet_ids.add(id(bet))

                if bet.is_contract_bet or not self.house_rules.leave_winning_bets_up:
                    self.bets.remove(bet)

                if bet.bet_type in ["All", "Tall", "Small"]:
                    self.bets.remove(bet)
                    if self.play_by_play:
                        self.play_by_play.write(f"  🏆 {bet.owner.name}'s {bet.bet_type} bet returned after win.")

                for attached in list(self.bets):
                    if attached.parent_bet == bet:
                        attached.owner.win_bet(attached, self.play_by_play)
                        self.bets.remove(attached)
                        settled_bets.append(attached)
                        resolved_bet_ids.add(id(attached))

            # ✅ Handle Moved Bets
            elif bet.status.startswith("move "):
                destination = int(bet.status.split()[1])
                bet.number = destination
                bet.status = "active"

            # ✅ Handle Returned Bets
            elif bet.status == "return":
                self.bets.remove(bet)
                settled_bets.append(bet)
                resolved_bet_ids.add(id(bet))

        # 🧹 Final pass: catch any orphaned odds bets whose parent was already removed
        for bet in list(self.bets):
            if bet.parent_bet and id(bet) not in resolved_bet_ids:
                if bet.status in {"lost", "return"}:
                    bet.owner.lose_bet(bet, self.play_by_play)
                elif bet.status == "won":
                    bet.owner.win_bet(bet, self.play_by_play)
                self.bets.remove(bet)
                settled_bets.append(bet)

        return settled_bets

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

    def has_odds_bet(self, linked_bet: Bet) -> bool:
        return any(
            b for b in self.bets
            if b.bet_type.endswith("Odds") and b.linked_bet == linked_bet
        )

    def total_risk(self) -> int:
        """Calculate total amount risked on the table for the current roll."""
        return sum(bet.amount for bet in self.bets)
