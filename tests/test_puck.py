import unittest
from craps.puck import Puck

class TestPuck(unittest.TestCase):
    def test_puck(self):
        puck = Puck()
        self.assertEqual(puck.position, "Off")
        self.assertIsNone(puck.point)

        puck.set_point(4)
        self.assertEqual(puck.position, "On")
        self.assertEqual(puck.point, 4)

        puck.reset()
        self.assertEqual(puck.position, "Off")
        self.assertIsNone(puck.point)

if __name__ == "__main__":
    unittest.main()