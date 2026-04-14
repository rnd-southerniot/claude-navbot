"""Unit tests for IMU reader pure helper functions.

Tests _compute_ypr (tilt-compensated heading), _wrap_pi, and _to_signed
from the L3GD20/LSM303D reader module.
"""

import math

import pytest

from navbot_imu.l3gd20_lsm303d_reader import (
    L3gd20Lsm303dReader,
    _compute_ypr,
    _wrap_pi,
)


class TestImuWrapPi:
    def test_zero(self):
        assert _wrap_pi(0.0) == 0.0

    def test_positive_within_range(self):
        assert abs(_wrap_pi(1.0) - 1.0) < 1e-9

    def test_two_pi_wraps_to_zero(self):
        assert abs(_wrap_pi(2.0 * math.pi)) < 1e-9

    def test_stays_in_range(self):
        for angle in [0.1, -0.1, 3.0, -3.0, 7.0, -7.0, 100.0]:
            result = _wrap_pi(angle)
            assert -math.pi <= result <= math.pi


class TestToSigned:
    """Test the static _to_signed method for 16-bit two's complement conversion."""

    def test_zero(self):
        assert L3gd20Lsm303dReader._to_signed(0) == 0

    def test_positive(self):
        assert L3gd20Lsm303dReader._to_signed(1000) == 1000

    def test_max_positive(self):
        assert L3gd20Lsm303dReader._to_signed(0x7FFF) == 32767

    def test_negative_one(self):
        assert L3gd20Lsm303dReader._to_signed(0xFFFF) == -1

    def test_min_negative(self):
        assert L3gd20Lsm303dReader._to_signed(0x8000) == -32768

    def test_minus_1000(self):
        # -1000 in 16-bit two's complement = 0xFC18
        assert L3gd20Lsm303dReader._to_signed(0xFC18) == -1000


class TestComputeYpr:
    """Test tilt-compensated YPR computation from accel + mag vectors."""

    def test_level_facing_x_positive(self):
        # Accelerometer: gravity along +Z (level)
        # Magnetometer: field along +X (facing magnetic north)
        accel = (0.0, 0.0, 1.0)
        mag = (1.0, 0.0, 0.0)
        yaw, pitch, roll = _compute_ypr(accel, mag)
        assert abs(pitch) < 0.01
        assert abs(roll) < 0.01
        assert abs(yaw) < 0.01  # facing north => yaw ~0

    def test_level_facing_y_positive(self):
        # Magnetometer field along +Y => yaw should be ~pi/2
        accel = (0.0, 0.0, 1.0)
        mag = (0.0, 1.0, 0.0)
        yaw, pitch, roll = _compute_ypr(accel, mag)
        assert abs(yaw - math.pi / 2.0) < 0.01

    def test_level_facing_negative_x(self):
        # Magnetometer field along -X => yaw should be ~pi
        accel = (0.0, 0.0, 1.0)
        mag = (-1.0, 0.0, 0.0)
        yaw, pitch, roll = _compute_ypr(accel, mag)
        assert abs(abs(yaw) - math.pi) < 0.01

    def test_pitch_nonzero_when_tilted_forward(self):
        # Tilt forward: gravity has -X component
        accel = (-1.0, 0.0, 1.0)
        mag = (1.0, 0.0, 0.0)
        yaw, pitch, roll = _compute_ypr(accel, mag)
        assert pitch > 0.1  # positive pitch for forward tilt

    def test_roll_nonzero_when_tilted_sideways(self):
        # Tilt sideways: gravity has +Y component
        accel = (0.0, 1.0, 1.0)
        mag = (1.0, 0.0, 0.0)
        yaw, pitch, roll = _compute_ypr(accel, mag)
        assert roll > 0.1  # positive roll for right tilt

    def test_output_yaw_within_pi(self):
        for accel, mag in [
            ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
            ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
            ((0.0, 0.0, 1.0), (-1.0, 0.0, 0.0)),
            ((0.0, 0.0, 1.0), (0.0, -1.0, 0.0)),
            ((-0.5, 0.3, 0.9), (0.5, 0.5, 0.1)),
        ]:
            yaw, _, _ = _compute_ypr(accel, mag)
            assert -math.pi <= yaw <= math.pi
