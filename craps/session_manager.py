from typing import Optional, Any
from config import HOUSE_RULES, ACTIVE_PLAYERS, DICE_TEST_PATTERNS
from craps.house_rules import HouseRules
from craps.log_manager import LogManager
from craps.play_by_play import PlayByPlay
from craps.rules_engine import RulesEngine
from craps.session_initializer import InitializeSession
from craps.lineup import PlayerLineup
from craps.dice import Dice
from craps.table import Table
from craps.roll_history_manager import RollHistoryManager
from craps.statistics import Statistics
from craps.game_state import GameState
from craps.player import Player


class SessionManager:
    def __init__(self) -> None:
        self.house_rules: Optional[HouseRules] = None
        self.table: Optional[Table] = None
        self.roll_history_manager: Optional[RollHistoryManager] = None
        self.log_manager: Optional[LogManager] = None
        self.play_by_play: Optional[PlayByPlay] = None
        self.rules_engine: Optional[RulesEngine] = None
        self.stats: Optional[Statistics] = None
        self.game_state: Optional[GameState] = None
        self.player_lineup: Optional[PlayerLineup] = None
        self.dice: Optional[Dice] = None
        self.initialized: bool = False
        self.locked: bool = False
        self.shooter_index: int = 0
        self.roll_history: list[dict[str, Any]] = []

    def setup_session(
        self,
        house_rules_dict: Optional[dict[str, Any]] = None,
        num_shooters: int = 10,
        num_players: int = 0,
        session_mode: str = "interactive",
        dice_mode: str = "live",
        roll_history_file: Optional[str] = None,
        pattern_name: Optional[str] = None
    ) -> bool:
        """
        Initializes core game components and prepares the session.
        """
        self.house_rules = HouseRules(house_rules_dict or HOUSE_RULES)
        self.play_by_play = PlayByPlay()
        self.log_manager = LogManager()
        self.rules_engine = RulesEngine()
        self.player_lineup = PlayerLineup(self.house_rules, None, self.play_by_play, self.rules_engine)

        # ✅ Initialize Dice
        if dice_mode == "history" and roll_history_file:
            self.dice = Dice(roll_history_file)
        else:
            self.dice = Dice()
            if dice_mode == "pattern" and pattern_name in DICE_TEST_PATTERNS:
                self.dice.forced_rolls.extend(DICE_TEST_PATTERNS[pattern_name])

        # ✅ Initialize Session
        session_initializer = InitializeSession(
            dice_mode=dice_mode,
            house_rules=self.house_rules,
            play_by_play=self.play_by_play,
            log_manager=self.log_manager,
            rules_engine=self.rules_engine,
            player_lineup=self.player_lineup
        )

        session_data = session_initializer.prepare_session(num_shooters, num_players)

        if session_data is None:
            return False

        (
            self.house_rules,
            self.table,
            self.roll_history_manager,
            self.log_manager,
            self.play_by_play,
            self.stats,
            self.game_state
        ) = session_data

        self.initialized = True
        return True

    def add_players_from_config(self) -> int:
        """
        Add players based on the ACTIVE_PLAYERS dict in config.py.
        UI or CLI setup should modify this config ahead of time.
        """
        if not self.player_lineup:
            raise RuntimeError("Session must be initialized before adding players.")

        players = [
            Player(name=player_name, strategy_name=strategy_name)
            for player_name, (strategy_name, enabled) in ACTIVE_PLAYERS.items() if enabled
        ]

        self.player_lineup.assign_strategies(players)
        return len(players)

    def lock_session(self) -> None:
        """
        Lock the session to prevent further changes to players or rules.
        """
        if not self.initialized:
            raise RuntimeError("Session must be initialized before it can be locked.")
        self.locked = True
        
        if not self.player_lineup or not self.play_by_play:
            raise RuntimeError("SessionManager is missing required components.")

        # Assign first shooter
        if self.player_lineup.get_active_players_list():
            shooter = self.player_lineup.get_active_players_list()[self.shooter_index]
            shooter.is_shooter = True
            if self.game_state:
                self.game_state.assign_new_shooter(shooter, self.shooter_index + 1)

    def accept_bets(self) -> int:
        if not self.locked:
            raise RuntimeError("Session must be locked before accepting bets.")
        if not self.play_by_play or not self.game_state or not self.table or not self.player_lineup:
            return 0

        self.play_by_play.write("  ---------- Place Your Bets! -------------")
        total_bets = 0

        for player in self.player_lineup.get_active_players_list():
            if not player.betting_strategy:
                continue

            bets = player.betting_strategy.place_bets(
                game_state=self.game_state,
                player=player,
                table=self.table
            )

            if bets:
                success = player.place_bet(
                    bets,
                    table=self.table,
                    phase=self.game_state.phase,
                    play_by_play=self.play_by_play
                )
                if success:
                    total_bets += len(bets) if isinstance(bets, list) else 1

        return total_bets

    def roll_dice(self) -> tuple[int, int]:
        if not (self.dice and self.stats and self.table and self.play_by_play and self.roll_history_manager and self.game_state and self.player_lineup):
            raise RuntimeError("SessionManager missing required components for rolling dice.")

        outcome = self.dice.roll()
        total = sum(outcome)

        players = self.player_lineup.get_active_players_list()
        shooter = players[self.shooter_index % len(players)]
        self.stats.update_rolls(total=total, table_risk=self.table.total_risk())
        self.stats.update_shooter_stats(shooter)

        roll_number = self.stats.session_rolls
        roll_message = f"  🎲 Roll #{roll_number} → {outcome} = {total}"
        self.play_by_play.write(roll_message)

        self.roll_history.append({
            "shooter_num": self.shooter_index + 1,
            "roll_number": roll_number,
            "dice": outcome,
            "total": total,
            "phase": self.game_state.phase,
            "point": self.game_state.point
        })

        return outcome
    
    def resolve_bets(self, outcome: tuple[int, int]) -> None:
        if not (self.table and self.game_state and self.stats and self.play_by_play and self.house_rules):
            raise RuntimeError("Missing components for resolving bets.")

        # Step 1: Check active bets
        self.table.check_bets(outcome, self.game_state.phase, self.game_state.point)

        # Step 2: Settle resolved bets
        resolved_bets = self.table.settle_resolved_bets()

        # Step 3: Update win/loss stats
        for bet in resolved_bets:
            self.stats.update_win_loss(bet)

            # Step 4: Notify strategy if bet won
            if bet.status == "won":
                payout = bet.resolved_payout
                strategy = getattr(bet.owner, "betting_strategy", None)
                if strategy and hasattr(strategy, "notify_payout"):
                    strategy.notify_payout(payout)

        # Step 5: Remove winning bets based on house rules
        for bet in resolved_bets:
            if bet.status == "won" and bet in self.table.bets:
                if bet.is_contract_bet or not self.house_rules.leave_winning_bets_up:
                    self.table.bets.remove(bet)
        
        # Step 6: Update game state
        previous_phase = self.game_state.phase
        state_message = self.game_state.update_state(outcome)
        self.play_by_play.write(state_message)

    def _rotate_shooter(self) -> None:
        if not self.player_lineup or not self.stats or not self.play_by_play:
            return

        players = self.player_lineup.get_active_players_list()
        if not players:
            return

        current_shooter = players[self.shooter_index % len(players)]
        current_shooter.reset_shooter()

        self.shooter_index += 1
        if self.shooter_index >= self.stats.num_shooters:
            self.play_by_play.write("🔚 Maximum number of shooters reached. Ending session.")
            self.locked = False
            return

        new_shooter = players[self.shooter_index % len(players)]
        new_shooter.is_shooter = True
        self.play_by_play.write(f"🎯 {new_shooter.name} is now the shooter.")

    def adjust_bets(self) -> None:
        """Let each strategy adjust bets after resolution (before next roll)."""
        if not self.game_state or not self.player_lineup or not self.table:
            raise RuntimeError("Missing game components for adjusting bets.")

        for player in self.player_lineup.get_active_players_list():
            strategy = getattr(player, "betting_strategy", None)
            if strategy and hasattr(strategy, "adjust_bets"):
                strategy.adjust_bets(self.game_state, player, self.table)
