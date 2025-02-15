import unittest
from craps.bets.field_bet import FieldBet
from craps.player import Player
from craps.table import Table
from craps.house_rules import HouseRules

class TestFieldBet(unittest.TestCase):
    def test_field_bet_outcomes(self):
        # Initialize house rules with custom payouts for 2 and 12
        house_rules = HouseRules()
        house_rules.set_field_bet_payouts((2, 1), (3, 1))  # 2:1 for 2, 3:1 for 12

        # Initialize player and table
        player = Player("Alice", 1000)
        table = Table(house_rules)

        # Define all possible dice totals and their expected outcomes
        test_cases = [
            # (dice_total, expected_status, expected_payout)
            (2, "won", 20),  # Field Bet wins 2:1 on 2 (house rules: 2:1)
            (3, "won", 10),  # Field Bet wins 1:1 on 3
            (4, "won", 10),  # Field Bet wins 1:1 on 4
            (5, "lost", 0),  # Field Bet loses on 5
            (6, "lost", 0),  # Field Bet loses on 6
            (7, "lost", 0),  # Field Bet loses on 7
            (8, "lost", 0),  # Field Bet loses on 8
            (9, "won", 10),  # Field Bet wins 1:1 on 9
            (10, "won", 10),  # Field Bet wins 1:1 on 10
            (11, "won", 10),  # Field Bet wins 1:1 on 11
            (12, "won", 30),  # Field Bet wins 3:1 on 12 (house rules: 3:1)
        ]

        # Print table header
        print("\nField Bet Test Results (House Rules: 2:1 for 2, 3:1 for 12)")
        print("=" * 70)
        print(f"{'Dice Total':<12} {'Expected Status':<16} {'Expected Payout':<16} {'Actual Status':<16} {'Actual Payout':<16} {'Result'}")

        # Test each dice total
        for dice_total, expected_status, expected_payout in test_cases:
            # Create a new Field Bet for each test case
            field_bet = FieldBet(10, player.name)
            player.place_bet(field_bet, table)

            # Simulate the dice roll
            dice_outcome = self._get_dice_outcome(dice_total)
            field_bet.resolve(dice_outcome, "come-out", None)

            # Resolve the bet and calculate the payout
            player.resolve_bets(table, None, dice_outcome, "come-out", None)

            # Get the actual status and payout
            actual_status = field_bet.status
            actual_payout = field_bet.payout()

            # Compare expected vs. actual
            status_match = actual_status == expected_status
            payout_match = actual_payout == expected_payout
            result = "✔" if status_match and payout_match else "✗"

            # Print the results in a table format
            print(f"{dice_total:<12} {expected_status:<16} ${expected_payout:<15} {actual_status:<16} ${actual_payout:<15} {result}")

    def _get_dice_outcome(self, total):
        """Helper method to generate a dice outcome for a given total."""
        if total < 2 or total > 12:
            raise ValueError("Invalid dice total. Must be between 2 and 12.")
        for die1 in range(1, 7):
            for die2 in range(1, 7):
                if die1 + die2 == total:
                    return [die1, die2]
        return None

if __name__ == "__main__":
    unittest.main()