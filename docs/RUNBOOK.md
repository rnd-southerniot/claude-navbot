# Runbook

## Build And Sync

```bash
cd /home/arif/projects/makerpi-rp2040-ros2-navbot
./scripts/sync_pi_repo.sh --hard --build
```

Use `--hard` only when GitHub should be treated as source truth and Pi-side source drift should be discarded. It does not remove ignored runtime outputs such as captures or `ros2_ws/install`.

Manual build:

```bash
cd /home/arif/projects/makerpi-rp2040-ros2-navbot
./scripts/build_ros2_ws.sh
```

Required runtime environment:

```bash
source /opt/ros/jazzy/setup.bash
source /home/arif/ros2_ws/install/setup.bash
source /home/arif/projects/makerpi-rp2040-ros2-navbot/ros2_ws/install/setup.bash
```

The external `/home/arif/ros2_ws/install/setup.bash` overlay provides the validated `sllidar_ros2` runtime.

## Launch

Base only:

```bash
ros2 launch navbot_bringup base.launch.py \
  serial_port:=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661410403114B35-if00
```

Base + LiDAR + INA238:

```bash
ros2 launch navbot_bringup base_lidar.launch.py
```

Base + LiDAR + INA238 + IMU + EKF:

```bash
ros2 launch navbot_bringup imu_localization.launch.py
```

Web console:

```bash
cd /home/arif/projects/makerpi-rp2040-ros2-navbot
./scripts/launch_web_console.sh port:=8081
```

Open:

```text
http://192.168.15.20:8081
```

SLAM:

```bash
./scripts/launch_slam.sh serial_port:=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661410403114B35-if00
```

For best C1 measurement accuracy, warm up the spinning LiDAR first:

```bash
LIDAR_WARMUP_SECONDS=120 ./scripts/launch_slam_with_warmup.sh serial_port:=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661410403114B35-if00
```

## Expected Devices

- RP2040:
  - `/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661410403114B35-if00`
- LiDAR serial/data adapter:
  - `/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0`
- INA238:
  - Pi `i2c-1`, address `0x40`
- IMU:
  - gyro `0x69`, accelerometer `0x19`, magnetometer `0x1E`

The RPLIDAR C1 is individually powered. USB is still required for the CP2102 serial/data link, and USB re-enumeration can still make `/scan` stale.

## Smoke Checks

```bash
ros2 node list | sort
ros2 topic info /scan
ros2 topic info /power/ina238/status
ros2 topic info /imu/l3gd20_lsm303d/raw
ros2 topic info /imu/l3gd20_lsm303d/ypr
ros2 topic info /heading_controller/status
ros2 topic info /odometry/filtered
ros2 topic hz /scan
ros2 topic hz /imu/l3gd20_lsm303d/raw
ros2 topic echo /imu/l3gd20_lsm303d/ypr --once
ros2 topic echo /odometry/filtered --once
curl -fsS http://127.0.0.1:8081/api/status | python3 -m json.tool
```

Healthy recent rates:

- `/scan`: about `10 Hz`
- `/imu/l3gd20_lsm303d/raw`: about `20 Hz`

## Ground-Test Procedure

1. Confirm estop and STOP are reachable.
2. Confirm the web console shows ROS, base, LiDAR, INA238, and IMU as live.
3. Start with wheels clear or on open ground.
4. Press and release `Forward`.
5. Press and release `Backward`.
6. Press and release `Rotate Left`.
7. Press and release `Rotate Right`.
8. Press red `STOP`.
9. Only continue to SLAM if `/scan`, `/odom`, `/joint_states`, and `/base/controller_state` stay fresh.

Validated cautious SLAM sequence:

1. stationary sanity
2. short forward
3. idle
4. short left turn
5. idle
6. short forward
7. idle
8. short right turn
9. idle
10. short backward
11. idle
12. final stop

## Capture Workflow

The web console records:

```text
/scan
/odom
/tf
/tf_static
/joint_states
/base/controller_state
/base/estop
/cmd_vel
/imu/l3gd20_lsm303d/raw
/imu/l3gd20_lsm303d/mag
/imu/l3gd20_lsm303d/ypr
/heading_controller/status
/odometry/filtered
```

Expected output:

```text
captures/YYYY-MM-DD_HH-MM-SS_<label>/
```

Each capture should contain `capture_meta.json`, `record.log`, and bag data under `bag/`.

## Troubleshooting

If `/scan` is stale but `sllidar_node` exists:

```bash
pid=$(pidof sllidar_node)
ls -l /proc/$pid/fd | grep tty
```

If the fd points to `/dev/ttyUSB* (deleted)`, the CP2102 serial/data adapter re-enumerated. Restart the launch so it reopens the by-id path.

If power telemetry is stale:

```bash
ros2 topic echo /power/ina238/status --once
i2cdetect -y 1
```

Expected INA238 address: `0x40`.

If Pi undervoltage appears in kernel logs, treat it as real hardware risk:

```bash
journalctl -k --since "10 min ago" --no-pager | grep -Ei "under.?voltage|voltage|cp210|ttyUSB|disconnect"
```

Do not continue broader motion or SLAM on an unstable supply path.
