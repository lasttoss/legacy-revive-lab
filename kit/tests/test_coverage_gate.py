"""Regression tests for the ratchet comparison.

The bug being guarded: 107/120 = 0.891666... compared as a raw float against a recorded
baseline of 0.8917 failed the gate on a run where nothing had changed.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coverage_gate import baseline_decimals, ratchet_dropped  # noqa: E402


class RatchetTest(unittest.TestCase):
    def test_same_ratio_four_decimals_is_not_a_drop(self):
        self.assertFalse(ratchet_dropped(107 / 120, 0.8917, 4))

    def test_same_ratio_three_decimals_is_not_a_drop(self):
        self.assertFalse(ratchet_dropped(107 / 120, 0.892, 3))

    def test_one_unit_below_the_recorded_precision_is_a_drop(self):
        self.assertTrue(ratchet_dropped(106 / 120, 0.8917, 4))

    def test_improvement_is_not_a_drop(self):
        self.assertFalse(ratchet_dropped(0.95, 0.8917, 4))

    def test_decimals_are_read_from_the_text(self):
        self.assertEqual(baseline_decimals("0.892"), 3)
        self.assertEqual(baseline_decimals("0.8917"), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
