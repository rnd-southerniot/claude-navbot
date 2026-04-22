# Navbot Project Status

**Last updated:** 2026-04-22 late evening (wheel_radius fix + straight-line verification)
**Branch:** `navbot-experimental`
**HEAD at update time:** `a4b9ebd` + wheel_radius fix + tolerance tighten + session docs (about to commit)
**Firmware version:** `1.3.0` with counter-drive + TEST_PWM + wheel_radius
  0.0325 m (matches URDF). Last-flashed binary on RP2040 is the build
  from this session's wheel_radius commit, flashed via BOOTSEL from
  Pi-mounted `/dev/sda1`.
**Key milestone commits:**
  `pre-counterdrive-code-v2` → `5185130` (FSM implemented, disabled) → `9b6d46a`
  (CD enabled) → `a65f008` (floor-validated 0.05 m/s) → `77375a2` (0.1 m/s) →
  `a445ffe` (STOP-CD bug fix, rotation validated) → `55badc6` (URDF wheel_offset_y
  calibrated to 0.091 m from empirical 360° rotation test).

This is the single source of truth for project state. It replaces
ad-hoc tracking of Phase C state in session transcripts. Update at the
end of each substantive session.

## Current State

The robot hardware is assembled and validated. First motion test
(120 mm straight drive at 0.05 m/s) succeeded with <1 mm odom error
against physical tape — see
[testing/motion-tests.md](testing/motion-tests.md). INA238 power
monitoring is live on System 1 (Pi rail). Foxglove bridge dashboard is
configured with a default layout committed
([operations/foxglove/README.md](operations/foxglove/README.md)). The
brake firmware experiment was reverted with full forensics committed
([notes/brake-attempt-forensic.md](notes/brake-attempt-forensic.md)).

## Active Work

No active work in-flight. Three Nav2 milestones completed across session 8:

1. **First autonomous nav goal SUCCESS** — three goals (1 m straight,
   0.3 m + 90°, return) all `STATUS_SUCCEEDED`, ~2.2 m total autonomous
   travel. Enabled by switching FollowPath DWB → RPP after two sessions
   of unsuccessful DWB critic tuning.
2. **4-step out-and-back sequence** — validated pure-rotation goals
   (steps 2 & 4) and round-trip composites. Observed visible curvature
   on forward legs; traced to firmware/URDF wheel_radius mismatch.
3. **`wheel_radius` fix + straight-line verification** — firmware
   0.033 → 0.0325 m (matches URDF). Mean commanded `ang.z` during
   forward translation dropped from +0.141 rad/s to ±0.014 rad/s
   (**10× reduction**); travel ratio improved from 70 % to 96–98 %
   of commanded. `xy_goal_tolerance` tightened 0.15 → 0.05 m.

Full records:
[first-nav-goal-success](validation/records/2026-04-22-first-nav-goal-success.md),
[four-step-sequence](validation/records/2026-04-22-nav2-four-step-sequence.md),
[wheel-radius-fix](validation/records/2026-04-22-wheel-radius-fix.md).

## Recent Milestones

- **2026-04-22 late evening — wheel_radius calibration fix + straight-
  line verification.** Firmware `LEFT_WHEEL_RADIUS_M` /
  `RIGHT_WHEEL_RADIUS_M` 0.033 → 0.0325 m (matches URDF). Rebuilt in
  [firmware/makerpi_rp2040_base/build/](firmware/makerpi_rp2040_base/build/),
  flashed via BOOTSEL (Pi-side mount of `/dev/sda1`, copy UF2, unmount —
  Pico auto-reboots to CDC in 2 s). `xy_goal_tolerance` tightened
  0.15 → 0.05 m now that odometry is calibrated. Two back-to-back
  0.5 m forward tests: mean `ang.z` during translation collapsed 10×
  (+0.141 → ±0.014 rad/s), travel ratio 70 → 96–98 %, XY convergence
  within 3–4 cm of goal. Full record:
  [validation/records/2026-04-22-wheel-radius-fix.md](validation/records/2026-04-22-wheel-radius-fix.md).
- **2026-04-22 late evening — 4-step out-and-back sequence.** Four
  goals (0.5 m fwd, 180° in place, 0.5 m fwd, 180° in place) all
  `STATUS_SUCCEEDED`. Pure in-place rotation goals validated: ang.z
  saturated at `rotate_to_heading_angular_vel: 0.5 rad/s` for 71
  samples with zero linear velocity. Net drift 12.6 cm / 18.8° over
  the round-trip, within the 4 × tolerance-stack budget but visible
  forward-leg curvature motivated the wheel_radius fix.
  [validation/records/2026-04-22-nav2-four-step-sequence.md](validation/records/2026-04-22-nav2-four-step-sequence.md).
- **2026-04-22 late evening — FIRST AUTONOMOUS NAV GOAL SUCCESS.**
  Three consecutive `navigate_to_pose` goals all returned
  `STATUS_SUCCEEDED`. Path: applied costmap inflation reductions
  (0.15 → 0.05 m in local_costmap, explicit 0.05 m in global_costmap
  overriding Nav2's 0.55 m default) and DWB `sim_time: 1.5 → 1.0 s`,
  then re-attempted — DWB still commanded zero forward velocity
  despite a 1.36 m clear forward corridor, confirming the controller
  was the blocker, not the costmap. Switched `FollowPath` from
  `dwb_core::DWBLocalPlanner` to
  `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController`.
  Three goals executed cleanly on the first attempt: 1.0 m straight
  (0.846 m actual, 85 % ratio matching motor envelope), 0.3 m + 90°
  composite (0.313 m + 77.5°), and 1.1 m + 84° return. RPP's
  `rotate_to_heading_angular_vel: 0.5 rad/s` and `desired_linear_vel:
  0.15 m/s` were both hit exactly by the robot. Full record:
  [validation/records/2026-04-22-first-nav-goal-success.md](validation/records/2026-04-22-first-nav-goal-success.md).
- **2026-04-22 evening Nav2 tuning + second nav-goal attempt (PARTIAL IMPROVED).**
  Phase 0 stepped cmd_vel tests showed motor has no real deadband (moves
  down to 0.005 m/s / 0.05 rad/s at 80 % of commanded). First Nav2 tuning
  (commit `7d1a33e`) with `min_speed_xy: 0.02` + `min_vel_x: 0.02`
  starved DWB's trajectory sampler ("No valid trajectories out of 0!") —
  BT fell back to spin recoveries. Fix (commit `dc04ba9`): remove
  `min_speed_xy`, restore `min_vel_x: 0`. Third attempt: DWB produced
  trajectories, robot executed commanded rotation toward goal (130° CCW
  in ~18 s), but forward translation still blocked by `ObstacleFootprint`
  critic rejecting forward samples that project into costmap inflation
  around LiDAR-seen obstacles at ~30 cm. Full analysis:
  [validation/records/2026-04-22-nav2-tuning-partial.md](validation/records/2026-04-22-nav2-tuning-partial.md).
- **2026-04-22 URDF calibration + first nav-goal attempt (PARTIAL).** Task 1
  applied wheel_offset_y 0.08 → 0.091 m per empirical rotation calibration
  (commit `55badc6`). Task 2 synced Pi repo from `8cf3319` → `55badc6` and
  rebuilt 12 packages (13.5 s, zero warnings). Task 3 launched full Nav2
  stack: SLAM + Nav2 lifecycle auto-activated cleanly with LiDAR on (no
  manual workaround like 2026-04-21 needed). DWB produces commands,
  velocity_smoother and collision_monitor propagate, base_bridge receives —
  **pipeline validated end-to-end**. Robot doesn't move because DWB's
  commanded velocity (~6.75 mm/s wheel tangential after smoothing) is below
  the motor's static-friction threshold. Full analysis:
  [validation/records/2026-04-22-first-nav-goal-partial.md](validation/records/2026-04-22-first-nav-goal-partial.md).
- **2026-04-22 First rotation test + STOP-handler bug fix.** 17 trials
  across 90°/180°/360° in both directions, all with CD active. Coast
  mean 9.58° at 90° CCW (10.60° CW — 1.11× symmetry), 18.35° at 180°,
  28° at 360°. Zero FAULT states. Discovered and fixed a CD-activation
  bug: `NAVBOT_CMD_STOP` was force-resetting CD state, which had been
  masked in Phase 5/6 because a timing race with firmware's internal
  timeout path let CD fire anyway. With commit `a445ffe`, STOP now
  yields to CD cleanly. 360° calibration gives empirical
  wheel_separation ≈ 0.182 m (vs firmware's 0.180 — 1.2% low, OK) and
  confirms URDF's 0.160 is wrong by 12%. Full record at
  [validation/records/2026-04-22-rotation-test.md](validation/records/2026-04-22-rotation-test.md).
- **2026-04-21 Counter-drive firmware DELIVERED.** Full design, implementation,
  bench validation, and floor validation at both 0.05 m/s and 0.1 m/s.
  Coast reduction **97 %** at 0.05 m/s (13.15 mm → 0.44 mm mean) and
  **~91 %** at 0.1 m/s (~52 mm KE-scaled baseline → 4.82 mm). Zero FAULT
  states across all trials. Tags: `pre-counterdrive-code-v2`,
  `counterdrive-enabled-v1`, `counterdrive-bench-validated-v1`,
  `pre-counterdrive-bench-v1`, `counterdrive-floor-validated-v1`,
  `counterdrive-floor-validated-0.1ms-v1`. Full record at
  [validation/records/2026-04-21-counter-drive-floor.md](validation/records/2026-04-21-counter-drive-floor.md).
- **2026-04-21 INA238 motor-rail relocation validated on bench.**
  Multi-input power-selector bypass identified; solved by raising motor
  battery to 6.3 V. Commit `ae32de3`. Unblocked counter-drive session.
- **2026-04-20 (counter-drive session, deferred at Phase 0.5c)**
  `TEST_PWM` bench debug command added (commit `f2b6877`, tag
  `pre-counterdrive-code-v1`). INA238 physically relocated to motor
  rail. Shunt-current readout unresolved at session close — resolved
  2026-04-21 with power-selector finding.
- **2026-04-20** INA238 driver header updated to cite SBOSA20C and
  document DEVICE_ID rev (commit `90ecee5`). Firmware banner bumped
  to 1.3.0 (commit `abba930`). Docs restructured into semantic
  subdirectories with migrated session knowledge (commit `ddbb9a7`).
  Package/firmware READMEs filled in (commit `78c9cfe`). Ops
  hardening commit `c73a297` added opt-in static-IP stanza in
  setup-pi.sh, RUNBOOK pre-flight safety checklist, and
  power-architecture doc.
- **2026-04-20** INA238 driver fix validated (commit `b309625`).
  False-positive root-caused: zero readings observed earlier were
  because the System 1 battery pack was OFF — driver itself is
  correct.
- **2026-04-20** Discovered Pi 5 USB-C and GPIO 5V OR-together through
  internal diodes (measured 0.94 A through INA238 shunt while Pi on
  USB-C). Documented in [power-architecture.md](power-architecture.md).
- **2026-04-19** Pi static IP `192.168.68.101` set via netplan;
  cloud-init network regen disabled.
- **2026-04-19** Pre-wipe kinematic calibration validated — EXCELLENT,
  no calibration changes needed
  ([validation/records/2026-04-19-pre-wipe-calibration.md](validation/records/2026-04-19-pre-wipe-calibration.md)).
- **2026-04-18** DWB rotation-only diagnosis session — full writeup
  at
  [validation/records/2026-04-18-dwb-rotation-session.md](validation/records/2026-04-18-dwb-rotation-session.md).
- **~2026-04** Pi rebuild (fastcdr ABI mismatch trigger) with 5 silent
  bugs fixed — see [hardware/pi-rebuild.md](hardware/pi-rebuild.md).
- **~2026-04** Brake firmware experiment attempted and reverted
  (commits `dc87008` attempted, `dc07888` archived). Forensic at
  [notes/brake-attempt-forensic.md](notes/brake-attempt-forensic.md).
- **2026-04-13** v1.2.0 validation freeze: 33/33 bench tests passed,
  10.8 h soak with 0 crashes / 0 disconnects / 0 checksum failures
  ([validation/records/2026-04-13-record.md](validation/records/2026-04-13-record.md)).

## Phase C Backlog

### Closed (this quarter)

- [x] Pi rebuild + 5 silent bugs fixed
- [x] First motion test (120 mm straight drive at 0.05 m/s)
- [x] Foxglove default layout committed
- [x] Brake firmware attempt + forensic documentation (reverted as ineffective)
- [x] INA238 driver fix (false-positive diagnosis + driver docstring update)
- [x] Pi static IP (`192.168.68.101` via netplan)
- [x] RUNBOOK pre-flight safety + incident response
- [x] `docs/power-architecture.md` with Pi USB-C non-isolation finding
- [x] `scripts/setup-pi.sh` static-IP stanza (opt-in via env var)
- [x] Docs restructure + session knowledge migration
- [x] Package and firmware READMEs
- [x] Firmware version bump convention codified (1.2.0 → 1.3.0)
- [x] **INA238 motor-rail validation** (multi-input power-selector finding)
- [x] **Active counter-drive firmware** — 5-state per-motor FSM with shared
      abort, HW watchdog, encoder-gated termination, 15 % PWM cap. Floor-
      validated at 0.05 m/s (coast 0.44 mm) and 0.1 m/s (coast 4.82 mm).
- [x] **Higher-speed motion test at 0.1 m/s** — Phase 6, 5 trials, clean pass
- [x] **First rotation test** — 2026-04-22. 17 trials at 90°/180°/360°
      in both directions with CD active. Coast 9.58° at 90° CCW (1.11×
      symmetry CW/CCW). Zero faults. Also discovered and fixed the
      STOP→CD bypass bug (commit `a445ffe`).
- [x] **STOP-handler CD bypass bug fix** — `NAVBOT_CMD_STOP` was calling
      `reset_counter_drive_both()`, short-circuiting CD activation when
      the Pi bridge sends STOP on zero cmd_vel. Fix removes the reset
      from STOP; ESTOP/RESET still reset CD.
- [x] **URDF `wheel_offset_y` 0.08 → 0.091 m** (commit `55badc6`).
- [x] **Pi repo sync** — Pi now at HEAD `55badc6`, 12 packages rebuilt.
- [x] **Firmware `wheel_radius` 0.033 → 0.0325 m** — matches URDF
      (commit this session). Verified: mean commanded `ang.z` during
      forward translation collapsed 10× (+0.141 → ±0.014 rad/s), travel
      ratio 70 → 96–98 %.

### Open — High Priority

- [x] **First autonomous navigation goal.** SUCCEEDED 2026-04-22 late
      evening. Three consecutive goals (1.0 m straight, 0.3 m + 90°,
      return to origin) all returned STATUS_SUCCEEDED. Costmap inflation
      reduced to 0.05 m and global_costmap plugins made explicit (Nav2
      default was 0.55 m inflation); FollowPath switched DWB → RPP. See
      [validation/records/2026-04-22-first-nav-goal-success.md](validation/records/2026-04-22-first-nav-goal-success.md).
- [ ] **Higher-speed motion test beyond 0.1 m/s** (0.2, 0.3 m/s). Current
      firmware CD parameters are conservative; may need to raise PWM cap
      or rebalance debounce for higher speeds.
- [ ] **Higher-precision wheel_separation calibration.** Tonight's "~11°
      short of start" was eyeball-level. A protractor laid at center of
      rotation, or a laser pointer with wall marks, would refine the
      0.182 m estimate to sub-degree precision.

### Open — Medium Priority

- [ ] **`/base/motor_voltage` topic now unreliable.** The GP27 ADC
      divider was physically disconnected during the 2026-04-20 INA238
      relocation. Topic currently reports ~0 V. Either restore the
      divider or deprecate the topic in favour of
      `/power/ina238/bus_voltage_v` (once INA238 motor-rail shunt
      diagnosis is resolved). Supersedes the earlier "C7 bug" item.
- [ ] **Pi-rail INA238 now absent** — the existing chip was relocated
      to the motor rail, so System 1 (Pi compute rail) currently has
      no current monitoring. A second INA238 (or restoration of this
      one after counter-drive work) is the medium-term fix.
- [ ] **RPP terminal rotate-to-goal-heading oscillation.** After the
      robot reaches `xy_goal_tolerance`, RPP's rotate-to-heading phase
      commits to a direction, saturates at `rotate_to_heading_angular_vel`,
      overshoots the target yaw by 50–90°, then damps back and
      oscillates until `yaw_goal_tolerance` fires. Reproduced in both
      post-wheel_radius-fix 0.5 m tests this session. Candidate fix:
      `rotate_to_heading_angular_vel: 0.5 → 0.3`,
      `max_angular_accel: 1.5 → 1.0`. Test separately, not tacked onto
      other config changes. Full observation:
      [validation/records/2026-04-22-wheel-radius-fix.md](validation/records/2026-04-22-wheel-radius-fix.md).
- [ ] **Pi-side CDRIVE telemetry parsing.** `navbot_serial_bridge`
      currently logs `WARN: unknown serial record: CDRIVE …` for every
      CD telemetry line. Add parsing + publish `/base/counter_drive_state`
      (std_msgs/String JSON-ified) per Phase 1 design plan. Not on safety
      path; forensic convenience.
- [ ] **Nav2 lifecycle auto-activation with LiDAR off.** When LiDAR
      power is off for bench-level testing, `lifecycle_manager_navigation`
      leaves `behavior_server`, `collision_monitor`, and `velocity_smoother`
      inactive (waiting on `/scan` or similar). Manual activation workaround
      is documented in [RUNBOOK.md](RUNBOOK.md). Fix is either (a) adjust
      Nav2 config to not block activation on `/scan` presence, or (b)
      document as permanent operator step for LiDAR-off sessions.
- [ ] **`scripts/launch_nav.sh` `set -u` bug.** The script's `set -euo
      pipefail` clashes with Jazzy's `setup.bash` which references
      `AMENT_TRACE_SETUP_FILES` before checking if it's set. Same
      workaround pattern as `setup-pi.sh` `configure_kernel_tuning()`.
      Fixed in Phase 7 commit.

### Open — Lower Priority

- [ ] **IMU integration (MPU-6050)** — ~10 hr. Adds a 6DOF IMU on top
      of the existing L3GD20+LSM303D cluster. Needed for reliable
      Nav2 rotation handling in real environments.
- [ ] **First navigation goal** — blocked on rotation test.
- [ ] **3D model integration** — awaiting CAD files.
- [ ] **NOPASSWD sudo removal** — needs physical keyboard access to
      the Pi to avoid locking out SSH.

## Known Issues / Gotchas

- **Pi USB-C does not isolate from System 1 battery rail.** Internal
  OR-diodes. Measured 0.94 A through INA238 shunt in this exact
  state (2026-04-20). See
  [power-architecture.md](power-architecture.md#important-usb-c-does-not-isolate-pi-from-this-system).
- **`/base/motor_voltage` reads rail-scaled**, not true battery voltage.
- **Nav2 `drive_on_heading` deceleration params are Kilted/Rolling
  only**, not Jazzy. Do not try to re-add them on Jazzy — reverted at
  commit `8cf3319`.
- **CP210x `-110` on control transfer `0x12`** from LiDAR is usually
  System 2 battery undervoltage, not a USB bus fault.
- **INA238 zero readings with driver healthy** → check System 1
  battery pack switch first. Zero readings do not imply a driver bug
  when the pack is OFF. See
  [hardware/ina238.md](hardware/ina238.md#troubleshooting-matrix).
- **`sllidar_node` holds deleted fd when CP2102 re-enumerates** →
  restart bringup; the node does not error out on its own.

## Decisions Log

- **`base_footprint` chosen as primary 2D nav frame** (commit
  `d7aa26c`). SLAM 33 mm offset was the smoking gun. Full rationale:
  [hardware/pi-rebuild.md](hardware/pi-rebuild.md) bug #3.
- **CycloneDDS chosen over FastDDS.** Required 16 MB kernel socket
  buffers (commit `9178451`) — baked into `setup-pi.sh` so future Pi
  rebuilds inherit the tuning.
- **LiDAR filter pipeline: `+Inf` → NaN, 16 m range cap** (commit
  `4565c25`). Per Slamtec guidance.
- **Foxglove bridge as primary dashboard**; `navbot_web` retained
  for the rosbag capture workflow until Foxglove covers that path.
- **Active counter-drive over regenerative brake** for creep-speed
  stop-on-command — regen brake was validated ineffective below a
  coast threshold that sits above our current motion envelope
  ([notes/brake-attempt-forensic.md](notes/brake-attempt-forensic.md)).
- **Firmware version bumps on every experiment-and-revert cycle**, not
  just net functional changes. Established 2026-04 along with the
  1.2.0 → 1.3.0 bump. See [../firmware/makerpi_rp2040_base/README.md](../firmware/makerpi_rp2040_base/README.md#firmware-version-banner).
- **Opt-in static-IP for setup-pi.sh** (`NAVBOT_CONFIGURE_STATIC_IP=1`)
  rather than default-on, so idempotent re-runs on a working Pi do
  not silently change networking.
- **Docs restructure into semantic subdirectories** (not numbered
  prefixes). Abandoned the partial `04-dashboards` / `06-validation`
  numbering experiment.

## References

- Full docs index: [index.md](index.md)
- Root project README: [../README.md](../README.md)
- Agent startup rules: [../AGENTS.md](../AGENTS.md)
