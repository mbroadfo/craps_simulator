from typing import Optional, Any
from config import HOUSE_RULES, DICE_TEST_PATTERNS
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
