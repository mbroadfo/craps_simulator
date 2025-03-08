from typing import List, Optional
from colorama import Fore, Style

class GameState:
    def __init__(self, stats, play_by_play=None):
        """
        Initialize the game state.

        :param stats: The Statistics object for recording game data.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        """
        self.point: Optional[int] = None  # Current point (None = come-out phase)
        self.previous_point: Optional[int] = None  # Track previous point for transitions
        self.stats = stats  # Statistics object
        self.play_by_play = play_by_play  # Log messages

    def set_table(self, table):
        """Set the table object reference."""
        self.table = table

    @property
    def phase(self) -> str:
        """Determine the game phase based on whether a point is set."""
        return "point" if self.point else "come-out"

    def update_state(self, dice_outcome: List[int]) -> str:
        """
        Update the game state based on the dice outcome.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :return: A message describing the state change.
        """
        total = sum(dice_outcome)
        self.previous_point = self.point  # Track previous point before changes
        message = "No change in game state."

        if self.phase == "come-out":
            if total in [7, 11]:  # Natural win
                self.point = None  # Ensure point is cleared
                message = f"{Fore.GREEN}✅ 7-Winner: Pass Line bets win! Puck is OFF.{Style.RESET_ALL}"
            elif total in [2, 3, 12]:  # Craps loss
                self.point = None
                message = f"{Fore.RED}❌ Craps: Pass Line bets lose! Puck is OFF.{Style.RESET_ALL}"
            else:  # Point is established
                self.point = total
                message = f"{Fore.YELLOW}Point Set: {total}. Puck is ON.{Style.RESET_ALL}"
        else:  # Point phase
            if total == self.point:  # Point hit, pass line wins
                self.stats.record_point_number_roll()
                self.point = None  # Reset back to come-out
                message = f"{Fore.GREEN}✅ Point Hit: {total}. Pass Line bets win! Puck is OFF.{Style.RESET_ALL}"
            elif total == 7:  # Seven out, pass line loses
                self.stats.record_seven_out()
                self.point = None
                message = f"{Fore.RED}❌ 7-Out: Pass Line bets lose! Puck is OFF.{Style.RESET_ALL}"

        if self.play_by_play:
            self.play_by_play.write(message)

        return message
