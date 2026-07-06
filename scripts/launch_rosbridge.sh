#!/usr/bin/env bash
# On-demand rosbridge WebSocket for ros-mcp (Claude Code <-> live ROS 2 control).
#
# ros-mcp connects to this WebSocket to list/echo topics, publish /cmd_vel, call
# services, and send Nav2 goals. See docs/operations/ros-mcp.md.
#
# SECURITY: rosbridge on :9090 is UNAUTHENTICATED ROS control. Anyone who can
# reach this port can publish /cmd_vel and drive the robot. Run it on-demand on
# a trusted LAN only and stop it (Ctrl-C) when done. For Pi-local Claude only,
# bind loopback:  scripts/launch_rosbridge.sh address:=127.0.0.1
#
# Usage:
#   scripts/launch_rosbridge.sh                        # ws://0.0.0.0:9090 (LAN — Mac can reach it)
#   scripts/launch_rosbridge.sh address:=127.0.0.1     # loopback only (Pi-local Claude)
#   scripts/launch_rosbridge.sh port:=9090
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=9090
ADDRESS=0.0.0.0
for arg in "$@"; do
  case "$arg" in
    port:=*)    PORT="${arg#port:=}" ;;
    address:=*) ADDRESS="${arg#address:=}" ;;
    *) echo "unknown arg: $arg (use port:=N address:=IP)" >&2 ;;
  esac
done

# Reclaim the port if a previous rosbridge is still listening (idempotent relaunch).
find_pids() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp "( sport = :${PORT} )" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u
  fi
}
pids="$(find_pids || true)"
if [[ -n "${pids}" ]]; then
  echo "Port ${PORT} already in use by PID(s): ${pids} — stopping..."
  kill ${pids} 2>/dev/null || true; sleep 1
  pids="$(find_pids || true)"; [[ -n "${pids}" ]] && { kill -9 ${pids} 2>/dev/null || true; sleep 1; }
fi

# Source the SAME ROS env as the navbot stack (DOMAIN 0 + CycloneDDS) so rosbridge
# sees the robot's topics. Running from a normal Pi login shell inherits these.
source /opt/ros/jazzy/setup.bash
[[ -f "${ROOT_DIR}/ros2_ws/install/setup.bash" ]] && source "${ROOT_DIR}/ros2_ws/install/setup.bash"

echo "Starting rosbridge on ws://${ADDRESS}:${PORT}  (ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-unset}, RMW=${RMW_IMPLEMENTATION:-default})"
echo "SECURITY: unauthenticated ROS control — trusted LAN only. Ctrl-C to stop."
exec ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:="${PORT}" address:="${ADDRESS}"
