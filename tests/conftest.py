"""Shared test configuration for navbot unit tests.

Adds ROS 2 package source directories to sys.path so that modules like
navbot_base can be imported without installing the ROS 2 packages.

Also provides lightweight stubs for rclpy and ROS 2 message types so
that modules which import them at the top level can be loaded in CI
without a full ROS 2 installation.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _ensure_stub(name):
    """Insert a MagicMock stub into sys.modules if the real module is missing."""
    if name not in sys.modules:
        sys.modules[name] = MagicMock()


# Stub out ROS 2 modules that are unavailable in CI.
_ROS2_STUBS = [
    "rclpy",
    "rclpy.node",
    "rclpy.executors",
    "geometry_msgs",
    "geometry_msgs.msg",
    "nav_msgs",
    "nav_msgs.msg",
    "sensor_msgs",
    "sensor_msgs.msg",
    "std_msgs",
    "std_msgs.msg",
    "tf2_ros",
    "smbus2",
]

for _mod in _ROS2_STUBS:
    _ensure_stub(_mod)

# Provide concrete lightweight stand-ins for message types that tests
# actually inspect (e.g. Quaternion fields, Bool.data, String.data).


class _Quaternion:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.w = 1.0


class _Bool:
    def __init__(self, data=False):
        self.data = data


class _String:
    def __init__(self, data=""):
        self.data = data


class _Float32:
    def __init__(self, data=0.0):
        self.data = data


class _Twist:
    def __init__(self):
        self.linear = types.SimpleNamespace(x=0.0, y=0.0, z=0.0)
        self.angular = types.SimpleNamespace(x=0.0, y=0.0, z=0.0)


class _Odometry:
    def __init__(self):
        self.header = types.SimpleNamespace(stamp=None, frame_id="")
        self.child_frame_id = ""
        self.pose = types.SimpleNamespace(
            pose=types.SimpleNamespace(
                position=types.SimpleNamespace(x=0.0, y=0.0, z=0.0),
                orientation=_Quaternion(),
            )
        )
        self.twist = types.SimpleNamespace(
            twist=types.SimpleNamespace(
                linear=types.SimpleNamespace(x=0.0, y=0.0, z=0.0),
                angular=types.SimpleNamespace(x=0.0, y=0.0, z=0.0),
            )
        )


class _JointState:
    def __init__(self):
        self.header = types.SimpleNamespace(stamp=None)
        self.name = []
        self.position = []
        self.velocity = []


class _TransformStamped:
    def __init__(self):
        self.header = types.SimpleNamespace(stamp=None, frame_id="")
        self.child_frame_id = ""
        self.transform = types.SimpleNamespace(
            translation=types.SimpleNamespace(x=0.0, y=0.0, z=0.0),
            rotation=_Quaternion(),
        )


# Patch the mock modules with our concrete message types.
sys.modules["geometry_msgs.msg"].Quaternion = _Quaternion
sys.modules["geometry_msgs.msg"].Twist = _Twist
sys.modules["geometry_msgs.msg"].TransformStamped = _TransformStamped
sys.modules["geometry_msgs.msg"].Vector3Stamped = MagicMock
sys.modules["nav_msgs.msg"].Odometry = _Odometry
sys.modules["sensor_msgs.msg"].JointState = _JointState
sys.modules["sensor_msgs.msg"].Imu = MagicMock
sys.modules["sensor_msgs.msg"].LaserScan = MagicMock
sys.modules["sensor_msgs.msg"].MagneticField = MagicMock
sys.modules["std_msgs.msg"].Bool = _Bool
sys.modules["std_msgs.msg"].String = _String
sys.modules["std_msgs.msg"].Float32 = _Float32
sys.modules["tf2_ros"].TransformBroadcaster = MagicMock

# Provide a stub Node base class so ROS 2 node classes can be defined.
_node_mod = sys.modules["rclpy.node"]
_node_mod.Node = type("Node", (), {"__init__": lambda self, *a, **kw: None})


# Add ROS 2 workspace source directories to sys.path.
_ROS2_SRC = Path(__file__).resolve().parent.parent / "ros2_ws" / "src"

for _pkg_dir in _ROS2_SRC.iterdir():
    if _pkg_dir.is_dir() and str(_pkg_dir) not in sys.path:
        sys.path.insert(0, str(_pkg_dir))
