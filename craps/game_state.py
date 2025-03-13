from typing import List, Optional, Any
from colorama import Fore, Style

class GameState:
    def __init__(self, stats: Any, play_by_play: Optional[Any] = None) -> None:
        """
        Initialize the game state.

        :param stats: The Statistics object for recording game data.
        :param play_by_play: The PlayByPlay instance for logging messages.
        """
        self._point: Optional[int] = None  # Encapsulated point
        self.previous_point: Optional[int] = None  # Track the last point before changes
        self.stats = stats
        self.play_by_play = play_by_play

    def set_table(self, table: Any) -> None:
        """Set the table reference."""
        self.table = table

    @property
    def point(self) -> Optional[int]:
        """Get the current point."""
        return self._point

    @point.setter
    def point(self, value: Optional[int]) -> None:
        """Set the point while tracking the previous point."""
        if self._point != value:
            self.previous_point = self._point  # Store previous point before change
            self._point = value  # Update point
            if self.play_by_play:
                self.play_by_play.write(f"GameState: Point changed from {self.previous_point} to {self._point}")

    @property
    def phase(self) -> str:
        """Determine the game phase based on whether a point is set."""
        return "point" if self._point else "come-out"

    @property
    def puck_on(self) -> bool:
        """Check if the puck should be 'ON' (point is set)."""
        return self._point is not None

    def update_state(self, dice_outcome: List[int]) -> str:
        """
        Update the game state based on the dice outcome.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :return: A message describing the state change.
        """
        total = sum(dice_outcome)
        message = "No change in game state."

        if self.phase == "come-out":
            if total in [7, 11]:  # Natural win
                self.point = None  # Reset to come-out phase
                message = f"{Fore.GREEN}✅ 7-Winner: Pass Line bets win! Puck is OFF.{Style.RESET_ALL}"
            elif total in [2, 3, 12]:  # Craps loss
                self.point = None  # Stay in come-out phase
                message = f"{Fore.RED}❌ Craps: Pass Line bets lose! Puck is OFF.{Style.RESET_ALL}"
            else:  # Set the point
                self.point = total
                message = f"{Fore.YELLOW}Point Set: {total}. Puck is ON.{Style.RESET_ALL}"
        else:  # Point phase
            if total == self.point:  # Point hit, pass line wins
                self.stats.record_point_number_roll()
                self.point = None  # Reset back to come-out
                message = f"{Fore.GREEN}✅ Point Hit: {total}. Pass Line bets win! Puck is OFF.{Style.RESET_ALL}"
            elif total == 7:  # Seven out, pass line loses
                self.stats.record_seven_out()
                self.point = None  # Reset back to come-out
                message = f"{Fore.RED}❌ 7-Out: Pass Line bets lose! Puck is OFF.{Style.RESET_ALL}"

        if self.play_by_play:
            self.play_by_play.write(message)

        return message
