from typing import List
from craps.puck import Puck
from colorama import Fore, Style

class GameState:
    def __init__(self, stats, play_by_play=None):
        """
        Initialize the game state.

        :param stats: The Statistics object for recording game data.
        :param play_by_play: The PlayByPlay instance for writing play-by-play messages.
        """
        self.phase = "come-out"  # Current game phase ("come-out" or "point")
        self.point = None  # Current point number (if in point phase)
        self.puck = Puck()  # Puck to indicate the point
        self.stats = stats  # Statistics object (required)
        self.play_by_play = play_by_play  # Store the PlayByPlay instance

    def set_table(self, table):
        """
        Set the table object.

        :param table: The table object.
        """
        self.table = table

    def update_state(self, dice_outcome: List[int]) -> str:
        """
        Update the game state based on the dice outcome.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :return: A message describing the state change.
        """
        total = sum(dice_outcome)
        previous_phase = self.phase
        message = "No change in game state."  # Default message

        if self.phase == "come-out":
            if total in [7, 11]:
                self.puck.reset()
                self.phase = "come-out"
                message = f"{Fore.GREEN}✅ 7-Winner: Pass Line bets win!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            elif total in [2, 3, 12]:
                self.puck.reset()
                self.phase = "come-out"
                message = f"{Fore.RED}❌ Craps: Pass Line bets lose!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            else:
                self.phase = "point"
                self.puck.set_point(total)
                self.point = total
                message = f"{Fore.YELLOW}Point Set: {total}. Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
                
                # Notify the table to reactivate inactive bets
                if self.table:
                    self.table.reactivate_inactive_bets()

        else:  # Point phase
            if total == self.point:
                self.stats.record_point_number_roll()
                self.puck.reset()
                self.phase = "come-out"
                self.point = None
                message = f"{Fore.GREEN}✅ Point Hit: {total}. Pass Line bets win!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            elif total == 7:
                self.stats.record_seven_out()  # Record 7-out
                self.puck.reset()
                self.phase = "come-out"
                self.point = None
                message = f"❌ 7-Out: Pass Line bets lose! Puck is {self.puck.position.upper()}."

                # Notify that a shooter transition should happen (handled externally)
                message += " 🚨🎲 Shooter change required!"

        # Log the phase transition for debugging
        print(f"[DEBUG] GameState updated: Total={total}, PrevPhase={previous_phase}, NewPhase={self.phase}, Point={self.point}")

        # Write the message to the play-by-play file
        if self.play_by_play:
            self.play_by_play.write(message)

        return message
