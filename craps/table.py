from typing import List, Optional, Set, Tuple, TYPE_CHECKING, Union
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

        # Upfront commission (vig_on_win=False tables): charged at
        # placement, non-refundable.
        if bet.vig and not self.house_rules.vig_on_win:
            commission = RulesEngine.calculate_vig(bet.bet_type, bet.amount, bet.number)
            bet.owner.balance -= commission
            if self.play_by_play:
                self.play_by_play.write(
                    f"  💸 {bet.owner.name} pays ${commission} commission to place the {bet.bet_type}."
                )
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

        # D6 availability: reject bets this table doesn't offer.
        availability = {
            "All": self.house_rules.ats_enabled,
            "Tall": self.house_rules.ats_enabled,
            "Small": self.house_rules.ats_enabled,
            "Hardways": self.house_rules.hardways_enabled,
            "Hop": self.house_rules.hop_bets_enabled,
            "Proposition": self.house_rules.prop_bets_enabled,
            "Any Craps": self.house_rules.prop_bets_enabled,
            "Horn": self.house_rules.prop_bets_enabled,
            "World": self.house_rules.prop_bets_enabled,
        }
        if not availability.get(bet.bet_type, True):
            return False, f"{bet.owner.name}'s {bet.bet_type} bet refused — this table does not offer {bet.bet_type} bets."

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

                bet.resolve(self.rules_engine, dice_outcome, game_state, self.house_rules)

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
                bet.resolve(self.rules_engine, dice_outcome, game_state, self.house_rules)

                if bet.status != original_status and bet.status in ("won", "lost", "return"):
                    resolved_bets.append(bet)

        return resolved_bets

    def _settle_attached(self, attached: Bet, settled_bets: List[Bet], resolved_bet_ids: Set[int]) -> None:
        """Settle one attached (odds) bet by its OWN resolved status,
        not its parent's — an odds bet that never actually won or lost
        (still "active"/"inactive" because it was off, or "return"
        because it's a Come Odds refunded on a come-out loss) must not
        be charged or paid just because its parent resolved. Shared by
        settle_resolved_bets()'s lost-parent and won-parent branches.
        """
        if attached.status == "lost":
            attached.owner.lose_bet(attached, self.play_by_play)
        elif attached.status == "won":
            attached.owner.win_bet(attached, self.play_by_play)
        else:
            # "return"/"active"/"inactive": no bankroll effect —
            # place_bet() never deducted it up front. Normalize to
            # "return" so whatever BetResolved reports is an honest,
            # single recognizable status for "refunded, not charged"
            # regardless of which of those three it happened to be —
            # the frontend renders a distinct "Returned" toast/feed
            # line for it, never a loss.
            attached.status = "return"
        self.bets.remove(attached)
        settled_bets.append(attached)
        resolved_bet_ids.add(id(attached))

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

                # Also settle attached odds bets — see _settle_attached
                # for why this follows each attached bet's OWN resolved
                # status, not the parent's.
                for attached in list(self.bets):
                    if attached.parent_bet == bet:
                        self._settle_attached(attached, settled_bets, resolved_bet_ids)

            # ✅ Handle Winning Bets
            elif bet.status == "won":
                bet.hits += 1
                if bet.vig and self.house_rules.vig_on_win:
                    # 5% commission collected from the winnings (never
                    # more than leaves $1 — protects payout()'s
                    # resolved_payout-is-set convention).
                    commission = min(
                        RulesEngine.calculate_vig(bet.bet_type, bet.amount, bet.number),
                        max(0, bet.resolved_payout - 1),
                    )
                    if commission > 0:
                        bet.resolved_payout -= commission
                        if self.play_by_play:
                            self.play_by_play.write(
                                f"  💸 {bet.owner.name} pays ${commission} commission on the winning {bet.bet_type}."
                            )
                bet.owner.win_bet(bet, self.play_by_play)
                settled_bets.append(bet)
                resolved_bet_ids.add(id(bet))

                if bet.is_contract_bet or not self.house_rules.leave_winning_bets_up:
                    self.bets.remove(bet)

                if bet.bet_type in ["All", "Tall", "Small"]:
                    self.bets.remove(bet)
                    if self.play_by_play:
                        self.play_by_play.write(f"  🏆 {bet.owner.name}'s {bet.bet_type} bet returned after win.")

                # _settle_attached again: an odds bet that was
                # "inactive" (off) when the number hit never actually
                # won — resolve_bet() never touched its status — so
                # it's returned, not paid.
                for attached in list(self.bets):
                    if attached.parent_bet == bet:
                        self._settle_attached(attached, settled_bets, resolved_bet_ids)

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

        # 🧹 Final pass. All odds bets now stay placed, exactly like
        # Place/Buy/Lay — a still-"active"/"inactive" one here simply
        # never resolved this roll and is left alone: no status
        # mutation, no removal, no event. refresh_bet_statuses()
        # (craps_engine.py) is what flips Come/Don't Come Odds between
        # active/inactive; Pass Line/Don't Pass Odds never toggle (they
        # always resolve the same roll as their parent, never spanning
        # a phase transition while still active) but now stay placed
        # too rather than being swept and re-placed every roll.
        #
        # This used to be scoped to only Come/Don't Come Odds: the
        # frozen v1 legacy strategies that place Pass Line/Don't Pass
        # Odds via FreeOddsStrategy either had no duplicate-placement
        # guard at all (IronCrossStrategy) or a guard comparing against
        # the *parent* bet's own `.number` (ThreePointMolly/Dolly/
        # PassLineStrategy) — which is always None for Pass Line/Don't
        # Pass (the point lives on game_state, not the bet), so the
        # guard silently never matched. The sweep was unintentionally
        # the only thing preventing those from duplicating every roll —
        # removing it reproducibly snowballed Pass Line Odds into extra
        # bets (confirmed via direct repro: two "Pass Line Odds 9" bets
        # on the same parent after one roll). Now fixed at the source
        # (those strategies key on parent identity instead, which is
        # correct for every bet type), so nothing here needs to special-
        # case bet_type anymore.
        #
        # Defensive catch-all: an odds bet whose OWN status resolved to
        # won/lost/return this roll but wasn't already swept up by its
        # parent's attached-bet loop above (shouldn't happen in normal
        # play — an odds bet only ever resolves the same roll its parent
        # does, and that branch already handles it) still gets settled
        # honestly here, following the same own-status rule as above.
        for bet in list(self.bets):
            if bet.parent_bet and id(bet) not in resolved_bet_ids:
                if bet.status == "lost":
                    bet.owner.lose_bet(bet, self.play_by_play)
                elif bet.status == "won":
                    bet.owner.win_bet(bet, self.play_by_play)
                elif bet.status == "return":
                    pass  # no bankroll effect — never deducted up front
                else:
                    continue  # still active/inactive: leave it placed
                settled_bets.append(bet)
                self.bets.remove(bet)

        return settled_bets

    def get_active_players(self) -> List["Player"]:
        """Retrieve all active players at the table."""
        return self.player_lineup.get_active_players_list()

    def has_odds_bet(self, linked_bet: Bet) -> bool:
        return any(
            b for b in self.bets
            if b.bet_type.endswith("Odds") and b.linked_bet == linked_bet
        )

    def total_risk(self) -> int:
        """Calculate total amount risked on the table for the current roll."""
        return sum(bet.amount for bet in self.bets)
