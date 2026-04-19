# Navbot Foxglove Layouts

Default layout for live Navbot visualization via `foxglove_bridge`. Replaces
the old `navbot_web` package.

## Load the default layout

1. Start the stack on the Pi (four separate terminals):

   ```bash
   # Terminal 1 — base + LiDAR
   ssh arif@192.168.68.101 \
     "bash -ic 'source ~/projects/claude-navbot/ros2_ws/install/setup.bash && \
      ros2 launch navbot_bringup base_lidar.launch.py'"

   # Terminal 2 — SLAM
   ssh arif@192.168.68.101 \
     "bash -ic 'source ~/projects/claude-navbot/ros2_ws/install/setup.bash && \
      ros2 launch navbot_slam slam_toolbox.launch.py'"

   # Terminal 3 — Nav2
   ssh arif@192.168.68.101 \
     "bash -ic 'source ~/projects/claude-navbot/ros2_ws/install/setup.bash && \
      ros2 launch navbot_navigation nav2.launch.py'"

   # Terminal 4 — Foxglove bridge
   ssh arif@192.168.68.101 \
     "bash -ic 'source /opt/ros/jazzy/setup.bash && \
      ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765 address:=0.0.0.0'"
   ```

2. Open <https://studio.foxglove.dev> (or the Foxglove Studio desktop app).

3. **Open connection** → **Foxglove WebSocket** → `ws://192.168.68.101:8765` → **Open**.

4. **Layouts** menu → **Import from file…** → select `navbot-default.json`.

## Panels in this layout

Left half: 3D scene.

- **3D scene** (`3D!1r53yko`) — `follow-pose` camera, grid, `/scan` (Turbo colormap on intensity), URDF loaded from the `/robot_state_publisher.robot_description` parameter.

Right half: four-panel tabbed overview.

- **`/base/motor_voltage`** plot — single-trace, colour `#f5774d`.
- **`/base/lidar_voltage`** plot — single-trace, colour `#4e98e2`.
- **`/base/serial_latency_ms`** plot — single-trace, colour `#f7df71`. Spikes here flag the RP2040↔Pi serial link stalling.
- **`/cmd_vel`** plot — 3 traces for `linear.x/y/z`. Flat at idle (no motion commands); populates during drive tests.
- **Diagnostic summary** — consumes `/diagnostics`; quiet until a node publishes `diagnostic_msgs/DiagnosticArray`.
- **`/dock_pose` raw messages** — placeholder for future docking work; empty when no dock is registered.

## Known cosmetic issues (Phase C)

- `/scan` shows Foxglove's black/magenta warning pattern on beams with no return. The RPLIDAR C1 emits `+Inf` for those and Foxglove flags them. Harmless — the valid points render correctly. Fix: add a `laser_filters::LaserScanRangeFilter` node to the bringup, or patch sllidar_ros2 to emit `NaN`.
- TF frame labels ("laser_link", "left_wheel_link", …) render large by default. Silence via 3D panel ⚙ → Scene → Labels off, or reduce Label size to `0.05`.

## When to update this layout

- New topic added that should be default-visible.
- Panel arrangement no longer matches workflow.
- Foxglove Studio major release with layout schema changes.

Re-export via Foxglove Studio → **Layouts** → **Export** (or copy JSON),
overwrite `navbot-default.json`, and commit.
