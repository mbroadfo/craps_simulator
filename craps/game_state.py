from typing import List, Optional, Any, Tuple
from colorama import Fore, Style
from craps.player import Player

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
        self.shooter: Optional[Player] = None  # Store current shooter (now a Player)

    def set_table(self, table: Any) -> None:
        """Set the table reference."""
        self.table = table

    def assign_new_shooter(self, shooter: Player, shooter_num: int) -> None:
        """
        Assigns a new shooter and resets their stats.

        :param shooter: The new shooter for the game.
        """
        self.shooter = shooter
        self.shooter_num = shooter_num
        self.shooter.is_shooter = True  # Mark player as the shooter
        if self.play_by_play:
            self.play_by_play.write("==============================================================================")
            self.play_by_play.write(f"🎲🎲 Shooter #{shooter_num}: {self.shooter.name} steps up!")

    def clear_shooter(self) -> None:
        """
        Clears the current shooter when a new shooter is needed.
        """
        if self.shooter:
            self.shooter.is_shooter = False
        self.shooter = None

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

    @property
    def phase(self) -> str:
        """Determine the game phase based on whether a point is set."""
        return "point" if self._point else "come-out"

    @property
    def puck_on(self) -> bool:
        """Check if the puck should be 'ON' (point is set)."""
        return self._point is not None

    def update_state(self, dice_outcome: Tuple[int, int]) -> str:
        """
        Update the game state based on the dice outcome.

        :param dice_outcome: The result of the dice roll (e.g., (3, 4)).
        :return: A message describing the state change.
        """
        total = sum(dice_outcome)
        message = "  No change in game state."

        if self.phase == "come-out":
            if total in [7, 11]:  # Natural win
                self.point = None  # Reset to come-out phase
                message = f"  ✅ 7-Winner: Pass Line bets win! → Puck OFF."
            elif total in [2, 3, 12]:  # Craps loss
                self.point = None  # Stay in come-out phase
                message = f"  ❌ Craps: Pass Line bets lose! → Puck OFF."
            else:  # Set the point
                self.point = total
                message = f"  🎯 Point Set to {total} → Puck ON"
        else:  # Point phase
            if total == self.point:  # Point hit, pass line wins
                self.stats.record_point_number_roll()
                self.point = None  # Reset b ck to come-out
                message = f"  ✅ Point Hit: {total} — Pass Line bets win! → Puck OFF"
            elif total == 7:  # Seven out, pass line loses
                self.stats.record_seven_out()
                self.point = None  # Reset back to come-out
                message = f"  ❌ 7-Out: Pass Line bets lose! → Puck OFF."

        return message
    
    def clear_point(self) -> None:
        """Clears the current point and resets phase to 'come-out'."""
        self.point = None

