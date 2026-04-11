#!/usr/bin/env bash
set -euo pipefail

echo "This script prints a suggested Ubuntu 24.04 + ROS 2 Jazzy setup flow."
echo "Review each command before running it on the target Raspberry Pi 5."
echo
cat <<'EOF'
sudo apt update
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-serial \
  python3-pip \
  python3-smbus2 \
  i2c-tools \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-tf2-ros \
  ros-jazzy-robot-localization \
  ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox \
  ros-jazzy-teleop-twist-keyboard

# Install an RPLIDAR ROS 2 driver compatible with the C1 on the Pi.
# This repository wraps the driver; it does not vendor it.

# If using the Adafruit INA238 module, verify /dev/i2c-1 exists and the device
# responds on the Pi I2C bus before adding ROS-side integration.
EOF
