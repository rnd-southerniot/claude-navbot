"""Unit tests for serial_bridge.py _handle_line protocol dispatch.

Tests the line-parsing logic that interprets firmware ODOM, ACK, ERR,
and STATE records. Uses a minimal mock node to avoid ROS 2 dependencies.
"""

import math

import pytest

from navbot_base.serial_bridge import SerialBridgeNode


class FakeMsg:
    """Minimal stand-in for a published ROS message."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakePublisher:
    """Records messages published through it."""

    def __init__(self):
        self.messages = []

    def publish(self, msg):
        self.messages.append(msg)


class FakeOdometry:
    """Minimal stand-in for DifferentialDriveOdometry."""

    def __init__(self):
        self.calls = []

    def update(self, **kwargs):
        self.calls.append(kwargs)

        class State:
            x = 0.0
            y = 0.0
            yaw = 0.0
            linear_velocity = 0.0
            angular_velocity = 0.0
            left_joint_position = 0.0
            right_joint_position = 0.0
            left_wheel_velocity = 0.0
            right_wheel_velocity = 0.0

        return State()


class FakeClock:
    class Now:
        def to_msg(self):
            return "fake_stamp"

    def now(self):
        return self.Now()


class FakeLogger:
    def __init__(self):
        self.warnings = []
        self.errors = []
        self.infos = []

    def warn(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def info(self, msg):
        self.infos.append(msg)


class StubBridgeNode:
    """Mimics SerialBridgeNode attributes used by _handle_line without ROS 2.

    We bind SerialBridgeNode._handle_line as a method on this stub so we can
    test the parsing logic in isolation.
    """

    def __init__(self):
        self.controller_state_pub = FakePublisher()
        self.estop_pub = FakePublisher()
        self.odom_pub = FakePublisher()
        self.joint_state_pub = FakePublisher()
        self.latency_pub = FakePublisher()
        self.tf_broadcaster = None
        self._odometry = FakeOdometry()
        self._firmware_version = None
        self._ping_sent_time = None
        self._last_latency_ms = None
        self._last_odom_time = None
        self._logger = FakeLogger()
        self.wheel_radius = 0.033
        self.odom_frame = "odom"
        self.base_frame = "base_footprint"
        self.publish_tf = False
        self._clock = FakeClock()

    def get_logger(self):
        return self._logger

    def get_clock(self):
        return self._clock

    # Bind the real method
    _handle_line = SerialBridgeNode._handle_line
    _publish_motion = SerialBridgeNode._publish_motion
    _publish_controller_state = SerialBridgeNode._publish_controller_state

    @staticmethod
    def _quaternion_from_yaw(yaw):
        return SerialBridgeNode._quaternion_from_yaw(yaw)


class TestHandleLineAck:
    def test_ack_ping_extracts_firmware_version(self):
        node = StubBridgeNode()
        node._handle_line("ACK PING v1.2.3")
        assert node._firmware_version == "v1.2.3"

    def test_ack_ping_without_version(self):
        node = StubBridgeNode()
        node._handle_line("ACK PING")
        assert node._firmware_version is None

    def test_ack_publishes_controller_state(self):
        node = StubBridgeNode()
        node._handle_line("ACK STOP")
        assert len(node.controller_state_pub.messages) == 1
        assert node.controller_state_pub.messages[0].data == "ACK STOP"

    def test_ack_ping_latency_measured(self):
        import time

        node = StubBridgeNode()
        node._ping_sent_time = time.monotonic() - 0.05  # 50ms ago
        node._handle_line("ACK PING v1.0")
        assert node._last_latency_ms is not None
        assert node._last_latency_ms > 0.0
        assert node._ping_sent_time is None  # cleared after measurement
        assert len(node.latency_pub.messages) == 1


class TestHandleLineOdom:
    def test_valid_odom_parsed(self):
        node = StubBridgeNode()
        node._handle_line("ODOM 12345 1000 1001 0.0500 0.0510")
        assert len(node._odometry.calls) == 1
        call = node._odometry.calls[0]
        assert call["stamp_sec"] == 12.345
        assert call["left_count"] == 1000
        assert call["right_count"] == 1001
        assert abs(call["left_velocity_mps"] - 0.05) < 1e-6
        assert abs(call["right_velocity_mps"] - 0.051) < 1e-6

    def test_malformed_odom_too_few_tokens(self):
        node = StubBridgeNode()
        node._handle_line("ODOM 12345 1000")
        assert len(node._odometry.calls) == 0
        assert len(node._logger.warnings) == 1

    def test_malformed_odom_non_numeric(self):
        node = StubBridgeNode()
        node._handle_line("ODOM abc 1000 1001 0.05 0.05")
        assert len(node._odometry.calls) == 0
        assert len(node._logger.warnings) == 1

    def test_odom_too_many_tokens(self):
        node = StubBridgeNode()
        node._handle_line("ODOM 12345 1000 1001 0.05 0.05 extra")
        assert len(node._odometry.calls) == 0


class TestHandleLineErr:
    def test_err_publishes_controller_state(self):
        node = StubBridgeNode()
        node._handle_line("ERR 01 motor stall detected")
        assert len(node.controller_state_pub.messages) == 1
        assert "ERR 01" in node.controller_state_pub.messages[0].data

    def test_err_estop_publishes_true(self):
        node = StubBridgeNode()
        node._handle_line("ERR ESTOP emergency stop active")
        assert len(node.estop_pub.messages) == 1
        assert node.estop_pub.messages[0].data is True

    def test_err_non_estop_publishes_false(self):
        node = StubBridgeNode()
        node._handle_line("ERR 01 motor stall detected")
        assert len(node.estop_pub.messages) == 1
        assert node.estop_pub.messages[0].data is False

    def test_malformed_err_too_few_tokens(self):
        node = StubBridgeNode()
        node._handle_line("ERR 01")
        assert len(node._logger.warnings) == 1
        assert len(node.controller_state_pub.messages) == 0


class TestHandleLineState:
    def test_state_publishes_controller_state(self):
        node = StubBridgeNode()
        node._handle_line("STATE RUNNING OK")
        assert len(node.controller_state_pub.messages) == 1
        assert node.controller_state_pub.messages[0].data == "RUNNING OK"

    def test_state_estop_publishes_true(self):
        node = StubBridgeNode()
        node._handle_line("STATE ESTOP hardware_triggered")
        assert len(node.estop_pub.messages) == 1
        assert node.estop_pub.messages[0].data is True

    def test_state_normal_publishes_false(self):
        node = StubBridgeNode()
        node._handle_line("STATE RUNNING OK")
        assert len(node.estop_pub.messages) == 1
        assert node.estop_pub.messages[0].data is False

    def test_malformed_state_too_few_tokens(self):
        node = StubBridgeNode()
        node._handle_line("STATE")
        assert len(node._logger.warnings) == 1


class TestHandleLineUnknown:
    def test_unknown_record_type_warns(self):
        node = StubBridgeNode()
        node._handle_line("FOOBAR 123")
        assert len(node._logger.warnings) == 1
        assert "unknown" in node._logger.warnings[0].lower()

    def test_empty_line_ignored(self):
        node = StubBridgeNode()
        node._handle_line("")
        assert len(node._logger.warnings) == 0
        assert len(node.controller_state_pub.messages) == 0


class TestQuaternionFromYaw:
    def test_zero_yaw(self):
        q = SerialBridgeNode._quaternion_from_yaw(0.0)
        assert abs(q.z) < 1e-9
        assert abs(q.w - 1.0) < 1e-9

    def test_90_degree_yaw(self):
        q = SerialBridgeNode._quaternion_from_yaw(math.pi / 2.0)
        assert abs(q.z - math.sin(math.pi / 4.0)) < 1e-6
        assert abs(q.w - math.cos(math.pi / 4.0)) < 1e-6
