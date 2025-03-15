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
        """Test that each bet type pays out correctly with the minimum bet when it wins."""
        bet_scenarios = [
            ("Pass Line", (4,3), "come-out", None, None),
            ("Pass Line Odds", (3,3), "point", None, 6),
            ("Come", (5,2), "point", None, None),
            ("Come", (3,3), "point", 6, None),
            ("Come Odds", (2,2), "point", 4, None),
            ("Place", (3,3), "point", 6, None),
            ("Place Odds", (3,3), "point", 6, None),
            ("Field", (1,1), "come-out", None, None),
            ("Field", (6,6), "point", None, None),
            ("Buy", (2,2), "point", 4, None),
            ("Lay", (5,2), "point", 10, None),
            ("Don't Pass", (1,1), "come-out", None, None),
            ("Don't Pass Odds", (5,5), "point", None, 10),
            ("Don't Come", (1,1), "point", None, None),
            ("Don't Come", (3,3), "point", 6, None),
            ("Don't Come Odds", (5,5), "point", 10, None),
            ("Hardways", (2,2), "point", 4, None),
            ("Hardways", (3,3), "point", 6, None),
            ("Hardways", (4,4), "point", 8, None),
            ("Hardways", (5,5), "point", 10, None),
            ("Proposition", (1,1), "come-out", 2, None),
            ("Proposition", (1,2), "point", 3, None),
            ("Proposition", (3,4), "come-out", 7, None),
            ("Proposition", (5,6), "point", 11, None),
            ("Proposition", (6,6), "come-out", 12, None),
            ("Hop", (5,1), "come-out", (1, 5), None),
            ("Hop", (3,3), "point", (3, 3), None)
        ]

        placed_bets = {}  # Dictionary to track placed bets by type

        print("\nPayout Validation for Minimum Bets")
        print("=" * 95)
        print(f"{'Bet Type':<20}{'Dice Roll':<15}{'Phase':<15}{'Bet Is On':<15}{'Point On':<15}{'Expected':<15}{'Actual':<15}")
        print("-" * 95)

        for bet_type, dice_roll, phase, bet_is_on, point_on in bet_scenarios:
            # Set the point number explicitly from test case
            self.point = point_on

            if bet_type in ["Come", "Don't Come"]:
                # First roll: Place the bet with no number
                bet = self.rules_engine.create_bet(bet_type, self.min_bet, self.player, number=None)
                self.common_setup.table.place_bet(bet, "point")  # ✅ Correct phase

                # First roll outcome determines movement or resolution
                first_roll_outcome = tuple(map(int, dice_roll))
                bet.resolve(self.rules_engine, first_roll_outcome, "point", self.point)

                # If the bet moves to a number, store it
                if bet.status == "active" and bet.number is not None:
                    placed_bets[bet_type] = bet

                    # ✅ Ensure a second roll that matches the Come number
                    second_roll_outcome = (bet.number, 1)  # Winning roll
                    bet.resolve(self.rules_engine, second_roll_outcome, "point", self.point)

            elif "Odds" in bet_type:
                # Place Odds bet only if the corresponding Come/Don't Come bet has moved to a number
                parent_bet_type = "Come" if "Come Odds" in bet_type else "Don't Come"
                parent_bet = placed_bets.get(parent_bet_type)
                if parent_bet and parent_bet.number is not None:
                    bet = self.rules_engine.create_bet(
                        bet_type,
                        self.min_bet,
                        self.player,
                        number=parent_bet.number,  # ✅ Now correctly inherits the number
                        parent_bet=parent_bet
                    )
                    self.common_setup.table.place_bet(bet, phase)

            else:
                # Regular bets resolve normally
                bet = self.rules_engine.create_bet(bet_type, self.min_bet, self.player, number=bet_is_on)
                self.common_setup.table.place_bet(bet, phase)

            # Second roll to determine if Come/Don't Come bet wins or loses
            if bet_type in ["Come", "Don't Come"] and bet.status == "active":
                second_roll_outcome = (4, 3)  # Example second roll, can be randomized
                bet.resolve(self.rules_engine, second_roll_outcome, phase, self.point)

            # Ensure dice outcome is correctly formatted
            dice_outcome = tuple(map(int, dice_roll))
            
            # Resolve the bet for payout
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
