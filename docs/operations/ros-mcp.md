# ros-mcp — Claude ↔ live ROS 2 control

`ros-mcp` ([robotmcp/ros-mcp-server](https://github.com/robotmcp/ros-mcp-server)) is
an MCP server that connects Claude Code to the navbot's **live ROS 2 graph** through
a **rosbridge WebSocket**. With it, Claude can list/echo topics, publish `/cmd_vel`,
call services, read sensors, and send Nav2 goals — directly, in real time.

> ⚠️ **SAFETY — this can move the robot.** ros-mcp can publish `/cmd_vel`, so an
> LLM turn can drive the wheels. Before using it for motion: **wheels on blocks or
> clear floor**, one small command at a time, keep the **ESTOP** reachable. And note
> the rosbridge port is **unauthenticated** (see [Security](#security)). Full rules
> in [Safety](#safety).

This is distinct from the `navbot-knowledge` SIoT-gateway MCP, which serves *static*
project knowledge. See [Relation to navbot-knowledge](#relation-to-navbot-knowledge).

## Architecture

```
                 stdio                         WebSocket ws://<host>:9090
Claude Code  ─────────────►  ros-mcp (uvx)  ──────────────────────────►  rosbridge_server  ──►  ROS 2 graph
 (Mac or Pi)                 MCP server                                   (on the Pi)            (DOMAIN 0 / CycloneDDS)

Two deployments (both installed):
  • Mac  → connect ws://192.168.68.126:9090   (remote control over the LAN)
  • Pi   → connect ws://127.0.0.1:9090         (Pi standalone / "does it alone")
```

- **ros-mcp** runs locally under each machine's Claude Code (stdio). It does **not**
  need ROS installed on that machine — it only needs to reach a rosbridge WebSocket.
- **rosbridge_server** runs **on the Pi** (the ROS machine), in the same ROS env as
  the navbot stack (`ROS_DOMAIN_ID=0`, CycloneDDS) so it sees the robot's topics.

## Install

### rosbridge on the Pi (once)
Installed by `scripts/setup-pi.sh` (package `ros-jazzy-rosbridge-suite`), or directly:
```bash
sudo apt install -y ros-jazzy-rosbridge-suite
```

### uv on the Pi (once)
`uvx` needs `uv` (per-user, no root). Installed by `setup-pi.sh`, or directly:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # → ~/.local/bin/uv
```
The Mac already has `uv`.

### Register ros-mcp with Claude Code (both machines)
The registration is **identical** on the Mac and the Pi — the rosbridge target is
chosen at runtime by the `connect` tool, not baked into the command:
```bash
claude mcp add ros-mcp -- uvx ros-mcp --transport=stdio
```
Verify: `claude mcp list` shows `ros-mcp`. (First launch downloads the package —
warm it once with `uvx ros-mcp --help` to avoid a slow first start.)

## Running rosbridge on the Pi

rosbridge is **on-demand by default** (it's an unauthenticated control surface —
don't leave it open). Two ways to run it:

**On-demand (recommended)** — start it when you want MCP control, Ctrl-C when done:
```bash
~/projects/claude-navbot/scripts/launch_rosbridge.sh              # ws://0.0.0.0:9090 (Mac can reach it)
~/projects/claude-navbot/scripts/launch_rosbridge.sh address:=127.0.0.1   # loopback only (Pi-local Claude)
```
The helper sources the navbot ROS env so rosbridge sees the robot's topics, and
reclaims :9090 on relaunch.

**Always-on (opt-in)** — a systemd unit is installed **disabled** by `setup-pi.sh`.
Enable only on a trusted LAN:
```bash
sudo systemctl enable --now navbot-rosbridge     # autostart at boot
sudo systemctl disable --now navbot-rosbridge    # back to on-demand
```

Confirm it's up: `ss -tlnp | grep 9090` and `pgrep -af rosbridge`.

## Connecting from Claude

Once `ros-mcp` is registered and rosbridge is running, tell Claude to connect, then
use the tools. Example:

> "Using ros-mcp, connect to the robot at `ws://192.168.68.126:9090`, then list the topics."

On the Pi standalone, use `ws://127.0.0.1:9090`.

### Tools ros-mcp exposes
| Tool | Purpose |
|------|---------|
| `connect` / `connect_to_robot` | Connect to a rosbridge (host + port 9090) |
| `get_topics` / `get_topics_details` / `get_topic_type` | Discover topics + message types |
| `get_services` / `get_services_details` / `call_service` | Discover + call services |
| `get_nodes` / `get_nodes_details` | Inspect the node graph |
| `publish_once` / `publish_for_durations` | Publish to a topic (one-shot or streamed for N s) |
| `subscribe_once` / `subscribe_for_duration` | Read topic samples |
| `send_action_goal` | Send an action goal (e.g. Nav2 `navigate_to_pose`) |
| (parameters, images) | Get/set params; fetch camera images |

## What it can drive on the navbot

| Topic / action | Type | Notes |
|----------------|------|-------|
| **`/cmd_vel`** | `geometry_msgs/Twist` | Drives the robot — `serial_bridge` subscribes; 0.5 s command timeout auto-stops |
| `/odom`, `/odometry/filtered` | `nav_msgs/Odometry` | Raw wheel odom / EKF-fused |
| `/scan` (+ `/scan_raw`) | `sensor_msgs/LaserScan` | Filtered scan SLAM/Nav2 use / raw from sllidar |
| `/imu/data` | `sensor_msgs/Imu` | Complementary-filter fused |
| `/power/ina238/status` | `std_msgs/String` (JSON) | Pi-rail voltage/current/power |
| `/joint_states`, `/base/*` | various | Wheel joints, estop, bridge health, latency |
| TF | — | `map → odom → base_footprint` (+ `laser_link`) |
| **`navigate_to_pose`** | Nav2 action | Send a goal pose (needs Nav2 running) |
| `/slam_toolbox/save_map` | service | Save a map during SLAM |

Bring these up on the Pi with the usual launches (`ros2 launch navbot_bringup
base.launch.py` / `base_lidar.launch.py` / `slam_imu.launch.py` / `localization.launch.py`).

## Example prompts

- "List all topics and their types."  → `get_topics_details`
- "Echo one `/odom` sample."  → `subscribe_once`
- "Echo `/power/ina238/status` once and tell me the bus voltage."
- "**Wheels are free** — publish `/cmd_vel` linear.x 0.05 for 0.5 s, then stop."  → `publish_for_durations`
- "Send a `navigate_to_pose` goal to x=1.0, y=0.0, yaw=0."  → `send_action_goal`
- "Call `/slam_toolbox/save_map` with name `home_v1`."

## Safety

ros-mcp is a **live actuation** surface — treat it like the `/navbot:*` motion
commands, not like a read-only query tool.

1. **Wheels free / clear space** before any `/cmd_vel` or `navigate_to_pose`. On blocks for bench work.
2. **One small command at a time.** Start with brief, low-speed motion; verify, then continue. (Mirrors the project's hardware-debugging rule.)
3. **Keep the ESTOP reachable** (GP20). The firmware's 0.5 s command timeout auto-stops if publishing stops.
4. **Prefer read-only first** (`get_topics`, `subscribe_once`) to confirm the graph before commanding motion.
5. Motion behaves exactly like `CMD_VEL` from the firmware protocol — same limits, same stall/estop handling (see [hardware reference in CLAUDE.md](../../CLAUDE.md)).

### Security
rosbridge on `:9090` bound to `0.0.0.0` is **unauthenticated** — anyone on
`192.168.68.0/24` who speaks rosbridge can publish `/cmd_vel` and drive the robot.

- Run **on-demand** and stop it when done (default; the systemd unit ships disabled).
- For Pi-local Claude only, bind **loopback**: `launch_rosbridge.sh address:=127.0.0.1`.
- Optionally UFW allow-list just the Mac's IP if you leave it running.
- **Never** run it on an untrusted/public network.

## Relation to navbot-knowledge

These are complementary MCP servers — use both:

| | `navbot-knowledge` (SIoT gateway) | `ros-mcp` |
|---|---|---|
| What | **Static** mirrored knowledge (skills, memory, docs) | **Live** ROS control + telemetry |
| Where | Gateway `10.10.8.113:8000` (prefix `nav`) | Local stdio under Claude Code (Mac/Pi) |
| Transport | HTTP via the gateway meta-tools | stdio → rosbridge WebSocket |
| Use it to | Look up how the robot works, past decisions, procedures | Actually query/drive the running robot |

Ask `navbot-knowledge` *how* to do something; use `ros-mcp` to *do* it on the live graph.

## Troubleshooting

- **Empty topic list after connect** → rosbridge isn't in the navbot ROS env. Ensure
  it was started via `launch_rosbridge.sh` (sources DOMAIN 0 + CycloneDDS), and that a
  navbot launch is actually running.
- **connect fails / refused** → rosbridge not running or wrong host/port; check
  `ss -tlnp | grep 9090` on the Pi and that the Mac can reach `192.168.68.126`.
- **ros-mcp "server failed to start"** → first `uvx` run is slow; warm with
  `uvx ros-mcp --help`, then retry `claude mcp list`.

## Related
- [operations/foxglove/README.md](foxglove/README.md) — Foxglove bridge (`:8765`, a
  *different* protocol; visualization, not ros-mcp).
- [operations/bench-test-commands.md](bench-test-commands.md) — the `/navbot:*` serial
  bench/motion commands (RP2040-direct, don't need ROS/rosbridge).
- [architecture/system.md](../architecture/system.md) — ROS graph, TF, topics.
