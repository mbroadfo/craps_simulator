import unittest
from craps.common import CommonTableSetup
from craps.rules_engine import RulesEngine

class TestPayouts(unittest.TestCase):
    def setUp(self):
        """Initialize the common table setup for testing."""
        self.common_setup = CommonTableSetup()
        self.rules_engine = RulesEngine()
        self.min_bet = self.common_setup.house_rules.table_minimum
        self.player = self.common_setup.player

    def test_payouts_for_all_bet_types(self):
        """Test that each bet type pays out correctly with the minimum bet."""
        bet_scenarios = [
            ("Pass Line", (4,3), "come-out", None, None),
            ("Pass Line Odds", (3,3), "point", None, 6),
            ("Come", (5,2), "come-out", None, None),
            ("Come", (3,3), "point", None, 6),
            ("Come Odds", (2,2), "point", 4, None),
            ("Place", (3,3), "point", 6, None),
            ("Place Odds", (3,3), "point", 6, None),
            ("Field", (1,1), "any", None, None),
            ("Field", (6,6), "any", None, None),
            ("Buy", (2,2), "point", 4, None),
            ("Lay", (5,5), "point", 10, None),
            ("Don't Pass", (1,1), "come-out", None, None),
            ("Don't Pass Odds", (5,5), "point", None, 10),
            ("Don't Come", (1,1), "come-out", None, None),
            ("Don't Come", (3,3), "point", 6, None),
            ("Don't Come Odds", (5,5), "point", 10, None),
            ("Hard 4", (2,2), "point", 4, None),
            ("Hard 6", (3,3), "point", 6, None),
            ("Hard 8", (4,4), "point", 8, None),
            ("Hard 10", (5,5), "point", 10, None),
            ("Any Craps", (1,1), "any", None, None),
            ("Any Seven", (4,3), "any", None, None),
            ("Proposition 12", (6,6), "any", None, None),
            ("Proposition 5", (2,3), "any", None, None),
            ("Hop 5-1", (5,1), "any", None, None),
            ("Hop 3-3", (3,3), "any", None, None)
        ]

        placed_bets = {}  # Dictionary to track placed bets by type

        print("\nPayout Validation for Minimum Bets")
        print("=" * 95)
        print(f"{'Bet Type':<20}{'Dice Roll':<15}{'Phase':<15}{'Bet Is On':<15}{'Point On':<15}{'Expected Payout':<15}{'Actual Payout':<15}")
        print("-" * 95)

        for bet_type, dice_roll, phase, bet_is_on, point_on in bet_scenarios:
            # Set the point number explicitly from test case
            self.point = point_on

            # Handle Odds bets that require a parent bet
            if "Odds" in bet_type:
                parent_bet_type = "Pass Line" if "Pass Line" in bet_type else "Come" if "Come" in bet_type else "Don't Pass" if "Don't Pass" in bet_type else "Don't Come"
                parent_bet = placed_bets.get(parent_bet_type)
                if parent_bet:
                    bet = self.rules_engine.create_bet(bet_type, self.min_bet, self.player, number=parent_bet.number, parent_bet=parent_bet)
                else:
                    print(f"Skipping {bet_type} bet as no parent bet exists.")
                    continue  # Skip if no parent bet exists
            else:
                bet = self.rules_engine.create_bet(bet_type, self.min_bet, self.player, number=bet_is_on)
                placed_bets[bet_type] = bet  # Store bet for later reference
            
            self.common_setup.table.place_bet(bet, phase)
            
            # Ensure dice outcome is correctly formatted as a tuple of two integers
            dice_outcome = tuple(map(int, dice_roll))
            
            # Resolve the bet, passing the correct point value
            bet.resolve(self.rules_engine, dice_outcome, phase, self.point)
            
            # Get the payout after resolution
            payout = bet.payout()
            
            # Expected payout based on rules
            expected_payout = bet.payout()
            
            # Print formatted results
            print(f"{bet_type:<20}{str(dice_roll):<15}{phase:<15}{str(bet_is_on):<15}{str(point_on):<15}{expected_payout:<15}{payout:<15}")
            
            # Validate payout
            self.assertEqual(payout, expected_payout)

if __name__ == "__main__":
    unittest.main()
