"""Launch the Pi-side IMU reader and an imu_complementary_filter that
publishes a fused orientation on /imu/data.

Pipeline:
  l3gd20_lsm303d_reader
    /imu/l3gd20_lsm303d/raw  (remap)-> /imu/data_raw
    /imu/l3gd20_lsm303d/mag  (remap)-> /imu/mag    (published but unused
                                                     while use_mag:=False)
  imu_complementary_filter
    subscribes: /imu/data_raw, /imu/mag
    publishes:  /imu/data

use_mag is disabled for this session — local magnetic field at axle
height measured 1.4 gauss (2.3× Earth's max), indicating a strong
local source (motor magnets). Gyro + accel fusion is sufficient for
short-term orientation; absolute heading reference via magnetometer
is deferred pending a hard-iron calibration pass.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    imu_config = PathJoinSubstitution(
        [FindPackageShare("navbot_imu"), "config", "l3gd20_lsm303d.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("log_level", default_value="info"),
            Node(
                package="navbot_imu",
                executable="l3gd20_lsm303d_reader",
                name="navbot_l3gd20_lsm303d_reader",
                output="screen",
                parameters=[imu_config],
                remappings=[
                    ("/imu/l3gd20_lsm303d/raw", "/imu/data_raw"),
                    ("/imu/l3gd20_lsm303d/mag", "/imu/mag"),
                ],
                arguments=["--ros-args", "--log-level", LaunchConfiguration("log_level")],
            ),
            Node(
                package="imu_complementary_filter",
                executable="complementary_filter_node",
                name="imu_complementary_filter",
                output="screen",
                parameters=[
                    {
                        "use_mag": False,
                        "do_bias_estimation": True,
                        "do_adaptive_gain": True,
                        "gain_acc": 0.01,
                        "gain_mag": 0.01,
                        "publish_tf": False,
                        "publish_debug_topics": False,
                        "fixed_frame": "odom",
                    }
                ],
            ),
        ]
    )
