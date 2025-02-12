from colorama import Fore, Style
class Puck:
    def __init__(self):
        self.position = "Off"
        self.point = None

    def set_point(self, value):
        self.position = "On"
        self.point = value
        print(f"{Fore.MAGENTA}Puck is now ON{Style.RESET_ALL}")

    def reset(self):
        self.position = "Off"
        self.point = None
        print(f"{Fore.MAGENTA}Puck is now OFF{Style.RESET_ALL}")