# Architecture

## System Split

The robot keeps deterministic wheel control on the Maker Pi RP2040 and runs ROS-facing coordination on the Raspberry Pi 5.

```text
Raspberry Pi 5, Ubuntu 24.04, ROS 2 Jazzy
  /cmd_vel -> navbot_base serial_bridge -> USB serial -> RP2040
  RP2040 telemetry -> /odom, /joint_states, /tf, /base/controller_state
  sllidar_ros2 -> /scan
  navbot_power -> /power/ina238/status
  navbot_imu -> /imu/l3gd20_lsm303d/*
  robot_localization -> /odometry/filtered
  slam_toolbox -> map -> odom
  navbot_web -> browser teleop, status, capture

Maker Pi RP2040
  motor PWM, encoder sampling, wheel PID, command timeout, estop, stall logic
```

## Hardware Truth

- Raspberry Pi 5 is the ROS computer.
- Maker Pi RP2040 is the low-level motor and encoder controller.
- RP2040 connects to the Pi by USB serial at `115200`.
- RPLIDAR C1: since 2026-06-25 it runs on its original USB adapter (CP2102N)
  powered from a Pi USB port. This requires `usb_max_current_enable=1` in
  `/boot/firmware/config.txt` (Pi 5 otherwise caps total USB at 600 mA and the
  LiDAR brownout drops other USB devices). LiDAR uses 460800 baud.
- LiDAR serial adapter by-id path:
  - `/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f05fca3b207fef1185c3221cedd322a4-if00-port0`
- INA238 is the only supported Pi-side power telemetry path in this repo.
- INA238 is on Pi `i2c-1` at `0x40` and publishes `/power/ina238/status`.
- The IMU is on Pi `i2c-1` with the detected split-address layout:
  - gyro `0x69`
  - accelerometer `0x19`
  - magnetometer `0x1E`

## Serial Protocol

Pi to RP2040:

```text
PING
STOP
RESET
ESTOP
CMD_VEL <linear_mps> <angular_rps>
WHEEL_VEL <left_mps> <right_mps>
```

RP2040 to Pi:

```text
ACK <command>
ERR <code> <message>
STATE <mode> <fault>
ODOM <stamp_ms> <left_count> <right_count> <left_vel_mps> <right_vel_mps>
```

The firmware must stop motion on command timeout even if the Pi keeps the serial port open. Estop and invalid actuator protection remain RP2040 responsibilities.

## ROS Topics

- `navbot_base`
  - subscribes: `/cmd_vel`
  - publishes: `/odom`, `/joint_states`, `/tf`, `/base/controller_state`, `/base/estop`
- `robot_state_publisher`
  - publishes: `/tf`, `/tf_static`
- `sllidar_ros2`
  - publishes: `/scan`
- `navbot_power`
  - publishes: `/power/ina238/*`
- `navbot_imu`
  - publishes: `/imu/l3gd20_lsm303d/raw`, `/imu/l3gd20_lsm303d/mag`, `/imu/l3gd20_lsm303d/status`
- `robot_localization`
  - publishes: `/odometry/filtered`
- `slam_toolbox`
  - publishes `map -> odom` during SLAM runs

## TF Tree

- `map -> odom`
- `odom -> base_footprint`
- `base_footprint -> base_link`
- `base_link -> laser_link`
- `base_link -> left_wheel_link`
- `base_link -> right_wheel_link`
- `base_link -> caster_link`

## Current Risks

- Pi undervoltage can destabilize USB devices and ROS telemetry.
- A stale LiDAR process can keep a ROS `/scan` publisher while holding a deleted `/dev/ttyUSB*` fd after CP2102 re-enumerates.
- Wheel radius, wheel separation, and counts-per-revolution still need final calibration.
- SLAM has a cautious small-area `GO`; larger map quality and Nav2 autonomy are not yet production-ready.
