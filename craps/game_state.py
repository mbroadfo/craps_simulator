# File: .\craps\game_state.py

from typing import List, Optional
from craps.puck import Puck
from colorama import Fore, Style
from craps.play_by_play import PlayByPlay  # Import the PlayByPlay class

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
        self.players = []  # List of players in the game (can be set later)
        self.shooter = None  # Current shooter
        self.stats = stats  # Statistics object (required)
        self.table = None  # Table object (can be set later)
        self.play_by_play = play_by_play  # Store the PlayByPlay instance

    def set_players(self, players: List) -> None:
        """
        Set the list of players in the game.

        :param players: The list of players.
        """
        self.players = players

    def set_table(self, table) -> None:
        """
        Set the table object.

        :param table: The table object.
        """
        self.table = table

    def set_shooter(self, shooter) -> None:
        """
        Set the current shooter and reset their statistics.

        :param shooter: The current shooter.
        """
        self.shooter = shooter
        self.shooter.reset_stats()
        message = f"\n{Fore.CYAN}New Shooter: {shooter.name}{Fore.YELLOW} Puck is {self.puck.position.upper()}{Style.RESET_ALL}"
        self.play_by_play.write(message)  # Write the message to the play-by-play file

    def update_state(self, dice_outcome: List[int]) -> str:
        """
        Update the game state based on the dice outcome.

        :param dice_outcome: The result of the dice roll (e.g., [3, 4]).
        :return: A message describing the state change.
        """
        total = sum(dice_outcome)
        message = "No change in game state."  # Default message

        if self.phase == "come-out":
            if total in [7, 11]:
                self.puck.reset()
                message = f"{Fore.GREEN}✅ 7-Winner: Pass Line bets win!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            elif total in [2, 3, 12]:
                self.puck.reset()
                message = f"{Fore.RED}❌ Craps: Pass Line bets lose!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            else:
                self.phase = "point"
                self.puck.set_point(total)
                self.point = total
                message = f"{Fore.YELLOW}Point Set: {total}. Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
                # Reactivate inactive Place bets
                reactivated_bets = []
                for player in self.players:
                    for bet in self.table.bets:
                        if bet.owner == player and bet.bet_type.startswith("Place") and bet.status == "inactive":
                            bet.status = "active"
                            reactivated_bets.append(f"{player.name}'s {bet.bet_type}")
                if reactivated_bets:
                    reactivated_message = f"{', '.join(reactivated_bets)} are now ON."
                    self.play_by_play.write(reactivated_message)  # Write the message to the play-by-play file
        else:  # Point phase
            if total == self.puck.point:
                self.shooter.points_rolled += 1  # Increment points rolled
                self.puck.reset()
                self.phase = "come-out"
                self.point = None
                message = f"{Fore.GREEN}✅ Point Hit: {total}. Pass Line bets win!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            elif total == 7:
                self.shooter.rolls_before_7_out = self.shooter.current_roll_count  # Record rolls before 7-out
                self.puck.reset()
                self.phase = "come-out"
                self.point = None
                message = f"{Fore.RED}❌ 7-Out: Pass Line bets lose!{Fore.YELLOW} Puck is {self.puck.position.upper()}.{Style.RESET_ALL}"
            elif total in [4, 5, 6, 8, 9, 10]:  # Point number rolled during point phase
                self.stats.record_point_number_roll()  # Record the roll number

        # Write the message to the play-by-play file
        self.play_by_play.write(message)

        return message

    def get_puck_state(self):
        if self.puck.position == "On":
            return f"Puck is ON (Point: {self.puck.point})"
        else:
            return "Puck is OFF (Come-out phase)"

    def __str__(self):
        return f"Game State: {self.get_puck_state()}"