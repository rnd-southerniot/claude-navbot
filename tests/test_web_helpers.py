"""Unit tests for navbot_web server.py pure helper functions.

Tests _yaw_from_quaternion, _safe_label, _json_safe, and _monotonic_age
which are used in the web console status pipeline.
"""

import math
import time

import pytest

from navbot_web.server import _json_safe, _monotonic_age, _safe_label, _yaw_from_quaternion


class TestYawFromQuaternion:
    def test_identity_quaternion(self):
        # No rotation: x=0, y=0, z=0, w=1 => yaw=0
        assert abs(_yaw_from_quaternion(0.0, 0.0, 0.0, 1.0)) < 1e-9

    def test_90_degree_yaw(self):
        # 90 deg about Z: z=sin(pi/4), w=cos(pi/4)
        z = math.sin(math.pi / 4.0)
        w = math.cos(math.pi / 4.0)
        yaw = _yaw_from_quaternion(0.0, 0.0, z, w)
        assert abs(yaw - math.pi / 2.0) < 1e-6

    def test_180_degree_yaw(self):
        # 180 deg about Z: z=sin(pi/2)=1, w=cos(pi/2)=0
        yaw = _yaw_from_quaternion(0.0, 0.0, 1.0, 0.0)
        assert abs(abs(yaw) - math.pi) < 1e-6

    def test_negative_90_degree_yaw(self):
        z = math.sin(-math.pi / 4.0)
        w = math.cos(-math.pi / 4.0)
        yaw = _yaw_from_quaternion(0.0, 0.0, z, w)
        assert abs(yaw - (-math.pi / 2.0)) < 1e-6

    def test_45_degree_yaw(self):
        angle = math.pi / 4.0
        z = math.sin(angle / 2.0)
        w = math.cos(angle / 2.0)
        yaw = _yaw_from_quaternion(0.0, 0.0, z, w)
        assert abs(yaw - angle) < 1e-6


class TestSafeLabel:
    def test_simple_label(self):
        assert _safe_label("ground_test") == "ground_test"

    def test_alphanumeric_with_hyphens(self):
        assert _safe_label("run-1") == "run-1"

    def test_special_characters_replaced(self):
        assert _safe_label("my test/run!") == "my_test_run_"

    def test_empty_string_defaults(self):
        assert _safe_label("") == "ground_test"

    def test_whitespace_only_defaults(self):
        assert _safe_label("   ") == "ground_test"

    def test_leading_trailing_whitespace_stripped(self):
        assert _safe_label("  hello  ") == "hello"

    def test_spaces_replaced(self):
        assert _safe_label("my label") == "my_label"


class TestJsonSafe:
    def test_finite_float_unchanged(self):
        assert _json_safe(1.5) == 1.5

    def test_nan_becomes_none(self):
        assert _json_safe(float("nan")) is None

    def test_inf_becomes_none(self):
        assert _json_safe(float("inf")) is None

    def test_negative_inf_becomes_none(self):
        assert _json_safe(float("-inf")) is None

    def test_string_unchanged(self):
        assert _json_safe("hello") == "hello"

    def test_int_unchanged(self):
        assert _json_safe(42) == 42

    def test_none_unchanged(self):
        assert _json_safe(None) is None

    def test_dict_recursion(self):
        result = _json_safe({"a": float("nan"), "b": 1.0})
        assert result == {"a": None, "b": 1.0}

    def test_list_recursion(self):
        result = _json_safe([1.0, float("inf"), "ok"])
        assert result == [1.0, None, "ok"]

    def test_nested_dict_in_list(self):
        result = _json_safe([{"x": float("nan")}])
        assert result == [{"x": None}]

    def test_nested_list_in_dict(self):
        result = _json_safe({"vals": [float("inf"), 2.0]})
        assert result == {"vals": [None, 2.0]}


class TestMonotonicAge:
    def test_none_returns_none(self):
        assert _monotonic_age(None) is None

    def test_recent_stamp_returns_small_positive(self):
        stamp = time.monotonic()
        age = _monotonic_age(stamp)
        assert age is not None
        assert 0.0 <= age < 1.0

    def test_old_stamp_returns_positive(self):
        stamp = time.monotonic() - 10.0
        age = _monotonic_age(stamp)
        assert age is not None
        assert age >= 9.0

    def test_future_stamp_clamped_to_zero(self):
        stamp = time.monotonic() + 100.0
        age = _monotonic_age(stamp)
        assert age == 0.0
