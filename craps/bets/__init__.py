# File: .\craps\bets\__init__.py

from craps.bet import Bet  # Import the base Bet class from craps.bet

# Import and re-export the bet classes
from .pass_line_bet import PassLineBet
from .place_bet import PlaceBet
from .free_odds_bet import FreeOddsBet
from .field_bet import FieldBet

# Optionally, define __all__ to make it clear which classes are exported
__all__ = ["Bet", "PassLineBet", "PlaceBet", "FreeOddsBet", "FieldBet"]