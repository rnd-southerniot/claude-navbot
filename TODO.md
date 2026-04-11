# TODO.md

## Immediate
- [ ] Re-validate short motion on a known-good power supply before more SLAM or autonomy work
- [ ] Re-run the short motion sequence while watching `/power/ina238/status` and capture any power-path correlation under load
- [ ] Decide whether INA238 scaling needs calibration against a trusted external meter
- [x] Wire the INA238 on Pi `i2c-1`, confirm `0x40`, and validate real voltage/current/power readings
- [x] Auto-launch `navbot_power/ina238_reader` from `base_lidar.launch.py`
- [x] Keep `navbot_web` rendering when optional telemetry is unavailable by emitting strict JSON `null` instead of `NaN`
- [x] Commit and push the by-id serial path defaults and serial-bridge reconnect hardening
- [x] Run the cautious small-area SLAM re-test with LiDAR live and capture enabled
- [x] Confirm `slam_toolbox` starts cleanly with the current working LiDAR path
- [x] Confirm `/map` appears and updates during the cautious motion sequence
- [x] Save the SLAM retest result back into repo docs
- [x] Verify the current Pi image uses the validated `sllidar_ros2` runtime and stable LiDAR by-id path
- [x] Commit and push the updated web-console launcher and refreshed docs
- [ ] Review capture evidence and decide whether any wheel/LiDAR calibration refinement is needed before broader autonomy work

## If hardware test fails
- [ ] If short motion pauses return only under load and `/scan` goes stale, stop and treat the power path as the primary suspect before revisiting web-console cadence or SLAM
- [ ] If base status stays stale, inspect serial port, base launch logs, and `/dev/ttyACM*`
- [ ] If LiDAR status stays stale, inspect `sllidar_ros2`, `/dev/serial/by-id/...`, and `/scan`
- [ ] If motion direction is wrong, re-check firmware wheel/sign mapping before more testing
- [ ] If stop-on-release or STOP fails, pause web-console testing and inspect `/cmd_vel` timeout behavior immediately
- [ ] If captures fail, inspect `record.log`, rosbag command invocation, and write permissions under `captures/`

## After first live pass
- [ ] Add clearer capture state and failure messaging in the web UI
- [ ] Add graceful stop/shutdown behavior for the web console process
- [ ] Show latest capture folder path in the UI
- [x] Show INA238 power telemetry in the web console
- [ ] Consider adding lightweight LiDAR preview after base behavior is proven stable
- [x] Re-run cautious SLAM retest with evidence capture if base + LiDAR + web console are stable

## Documentation cleanup
- [x] Update root `README.md` to stop describing firmware as mostly scaffold/TODO-only
- [x] Add a short Pi operator runbook section referencing `navbot_web`
- [x] Save any newly verified serial port, wheel-sign, launch quirks, LiDAR dependency reality, and capture evidence into standard repo docs
