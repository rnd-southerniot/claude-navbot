# navbot_imu

Pi-side reader for the L3GD20 (gyroscope) + LSM303D (accelerometer +
magnetometer) IMU cluster on Pi I²C bus 1.

## Nodes / Executables

- `l3gd20_lsm303d_reader` — polls the three I²C devices and publishes
  raw + derived topics.

## Topics

Published:

- `/imu/l3gd20_lsm303d/raw` (sensor_msgs/Imu) — raw gyro + accel at
  ~20 Hz.
- `/imu/l3gd20_lsm303d/mag` (sensor_msgs/MagneticField) — raw magneto.
- `/imu/l3gd20_lsm303d/ypr` (geometry_msgs/Vector3) — compass-derived
  yaw/pitch/roll.
- `/imu/l3gd20_lsm303d/status` (std_msgs/String) — JSON status
  envelope (includes `available` flag).

## I²C addresses

- Gyro: `0x69`
- Accelerometer: `0x19`
- Magnetometer: `0x1E`

Verify with `i2cdetect -y 1`.

## Dependencies

- ROS 2 Jazzy: `rclpy`, `sensor_msgs`, `geometry_msgs`, `std_msgs`.
- External: `smbus2`.
- Hardware: L3GD20 + LSM303D breakout on Pi I²C-1.

## Launch

```bash
ros2 launch navbot_imu imu.launch.py
```

Also auto-launched by `navbot_bringup/imu_localization.launch.py`.

## Related docs

- Runbook: [../../../docs/RUNBOOK.md](../../../docs/RUNBOOK.md)
- Architecture: [../../../docs/architecture/system.md](../../../docs/architecture/system.md)
