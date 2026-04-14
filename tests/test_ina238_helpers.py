"""Unit tests for INA238 power monitor pure helper functions.

Tests _to_signed and _dietemp_celsius register decoding from the
INA238 reader module.
"""

import pytest

from navbot_power.ina238_reader import Ina238Reader


class TestIna238ToSigned:
    """16-bit two's complement conversion used for current/shunt registers."""

    def test_zero(self):
        assert Ina238Reader._to_signed(0) == 0

    def test_positive(self):
        assert Ina238Reader._to_signed(500) == 500

    def test_max_positive(self):
        assert Ina238Reader._to_signed(0x7FFF) == 32767

    def test_negative_one(self):
        assert Ina238Reader._to_signed(0xFFFF) == -1

    def test_min_negative(self):
        assert Ina238Reader._to_signed(0x8000) == -32768

    def test_known_negative(self):
        # -100 in 16-bit two's complement = 0xFF9C
        assert Ina238Reader._to_signed(0xFF9C) == -100


class TestDietempCelsius:
    """Temperature register decoding per INA238 datasheet.

    Register format: 12-bit signed value in bits [15:4], LSB = 0.125 C.
    """

    def test_zero(self):
        assert Ina238Reader._dietemp_celsius(0x0000) == 0.0

    def test_25_degrees(self):
        # 25.0 / 0.125 = 200, shifted left 4 => 200 << 4 = 0x0C80
        raw = 200 << 4
        assert abs(Ina238Reader._dietemp_celsius(raw) - 25.0) < 0.001

    def test_negative_temperature(self):
        # -10.0 / 0.125 = -80
        # 12-bit two's complement of -80: 0xFB0, shifted left 4 => 0xFB00
        value_12bit = (-80) & 0xFFF  # 0xFB0
        raw = value_12bit << 4
        assert abs(Ina238Reader._dietemp_celsius(raw) - (-10.0)) < 0.001

    def test_max_positive_temp(self):
        # Max 12-bit positive: 0x7FF = 2047, temp = 2047 * 0.125 = 255.875
        raw = 0x7FF << 4
        assert abs(Ina238Reader._dietemp_celsius(raw) - 255.875) < 0.001

    def test_small_positive(self):
        # 1 LSB = 0.125 C
        raw = 1 << 4
        assert abs(Ina238Reader._dietemp_celsius(raw) - 0.125) < 0.001


class TestIna238Init:
    """Verify shunt calibration and LSB calculations."""

    def test_current_lsb(self):
        reader = Ina238Reader(i2c_bus=1, address=0x40, shunt_resistance_ohm=0.015, max_current_a=10.0)
        expected_lsb = 10.0 / 32768.0
        assert abs(reader.current_lsb - expected_lsb) < 1e-12

    def test_power_lsb(self):
        reader = Ina238Reader(i2c_bus=1, address=0x40, shunt_resistance_ohm=0.015, max_current_a=10.0)
        assert abs(reader.power_lsb - reader.current_lsb * 0.2) < 1e-12

    def test_shunt_cal_within_range(self):
        reader = Ina238Reader(i2c_bus=1, address=0x40, shunt_resistance_ohm=0.015, max_current_a=10.0)
        assert 1 <= reader.shunt_cal <= 0xFFFF
