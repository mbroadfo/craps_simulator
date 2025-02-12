from colorama import Fore, Style
from craps.puck import Puck

class GameState:
    def __init__(self, stats, players):
        """
        Initialize the game state.
        
        :param stats: The Statistics object to track point number rolls.
        :param players: The list of players in the game.
        """
        self.phase = "come-out"
        self.point = None
        self.puck = Puck()
        self.shooter = None
        self.stats = stats  # Store the stats object
        self.players = players  # Store the players list

    def set_shooter(self, shooter):
        """Set the current shooter and reset their statistics."""
        self.shooter = shooter
        self.shooter.reset_stats()

    def update_state(self, dice_outcome):
        """Update the game state based on the dice outcome."""
        total = sum(dice_outcome)
        message = None

        if self.phase == "come-out":
            if total in [7, 11]:
                self.puck.reset()
                message = f"{Fore.GREEN}✅ 7-Winner: Pass Line bets won!{Style.RESET_ALL}"
            elif total in [2, 3, 12]:
                self.puck.reset()
                message = f"{Fore.RED}❌ Craps: Pass Line bets lose!{Style.RESET_ALL}"
            else:
                self.phase = "point"
                self.puck.set_point(total)
                self.point = total
                message = f"{Fore.YELLOW}Point Set: {total}{Style.RESET_ALL}"
                # Reactivate inactive Place bets
                for player in self.players:
                    for bet in player.active_bets:
                        if bet.bet_type.startswith("Place") and bet.status == "inactive":
                            bet.status = "active"
                            print(f"{player.name}'s {bet.bet_type} bet is now ACTIVE.")
        else:  # Point phase
            if total == self.puck.point:
                self.shooter.points_rolled += 1  # Increment points rolled
                self.puck.reset()
                self.phase = "come-out"
                self.point = None
                message = f"{Fore.GREEN}✅ Point Hit: {total}. Pass Line bets win!{Style.RESET_ALL}"
            elif total == 7:
                self.shooter.rolls_before_7_out = self.shooter.current_roll_count  # Record rolls before 7-out
                self.puck.reset()
                self.phase = "come-out"
                self.point = None
                message = f"{Fore.RED}❌ 7-Out: Pass Line bets lose!{Style.RESET_ALL}"
            elif total in [4, 5, 6, 8, 9, 10]:  # Point number rolled during point phase
                self.stats.record_point_number_roll()  # Record the roll number

        return message

    def get_puck_state(self):
        if self.puck.position == "On":
            return f"Puck is ON (Point: {self.puck.point})"
        else:
            return "Puck is OFF (Come-out phase)"

    def __str__(self):
        return f"Game State: {self.get_puck_state()}"