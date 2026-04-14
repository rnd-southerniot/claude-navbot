"""Unit tests for heading_controller.py pure helper functions.

Tests _wrap_pi and _clamp which are used in the closed-loop
heading control loop.
"""

import math

from navbot_base.heading_controller import _clamp, _wrap_pi


class TestWrapPi:
    def test_zero(self):
        assert _wrap_pi(0.0) == 0.0

    def test_pi_wraps_to_pi(self):
        result = _wrap_pi(math.pi)
        assert abs(result - math.pi) < 1e-9 or abs(result + math.pi) < 1e-9

    def test_negative_pi(self):
        result = _wrap_pi(-math.pi)
        assert abs(result - math.pi) < 1e-9 or abs(result + math.pi) < 1e-9

    def test_two_pi_wraps_to_zero(self):
        assert abs(_wrap_pi(2.0 * math.pi)) < 1e-9

    def test_three_halves_pi_wraps_negative(self):
        result = _wrap_pi(1.5 * math.pi)
        assert abs(result - (-math.pi / 2.0)) < 1e-9

    def test_negative_three_halves_pi(self):
        result = _wrap_pi(-1.5 * math.pi)
        assert abs(result - (math.pi / 2.0)) < 1e-9

    def test_large_positive(self):
        result = _wrap_pi(10.0 * math.pi + 0.5)
        assert -math.pi <= result <= math.pi
        assert abs(result - 0.5) < 1e-9

    def test_large_negative(self):
        result = _wrap_pi(-10.0 * math.pi - 0.5)
        assert -math.pi <= result <= math.pi
        assert abs(result - (-0.5)) < 1e-9

    def test_quarter_pi(self):
        assert abs(_wrap_pi(math.pi / 4.0) - math.pi / 4.0) < 1e-9


class TestClamp:
    def test_within_range(self):
        assert _clamp(0.5, 0.0, 1.0) == 0.5

    def test_at_low_bound(self):
        assert _clamp(0.0, 0.0, 1.0) == 0.0

    def test_at_high_bound(self):
        assert _clamp(1.0, 0.0, 1.0) == 1.0

    def test_below_low_bound(self):
        assert _clamp(-1.0, 0.0, 1.0) == 0.0

    def test_above_high_bound(self):
        assert _clamp(5.0, 0.0, 1.0) == 1.0

    def test_negative_range(self):
        assert _clamp(0.0, -2.0, -1.0) == -1.0

    def test_symmetric_range(self):
        assert _clamp(-0.5, -1.0, 1.0) == -0.5
        assert _clamp(1.5, -1.0, 1.0) == 1.0
        assert _clamp(-1.5, -1.0, 1.0) == -1.0
