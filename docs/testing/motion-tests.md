# Motion Tests

Documented motion-test results for the Navbot platform. Each test is
reproducible; values below are what was actually measured, not targets.

For the broader project state and the list of pending tests, see
[../project-status.md](../project-status.md).

## First motion test — 120 mm forward drive

### Test configuration

- **Nav2 action:** `drive_on_heading`
- **Command:** `target.x = 0.10 m`, `speed = 0.05 m/s`
- **Commanded travel:** 100 mm
- **Surface:** indoor lab floor
- **Firmware:** 1.2.0 (this version was baseline; see
  [../../firmware/makerpi_rp2040_base/include/navbot_protocol.h](../../firmware/makerpi_rp2040_base/include/navbot_protocol.h)
  for the current version on subsequent tests)
- **Wheel radius (URDF):** `0.0325 m`

### Results

| Metric | Value |
|---|---|
| Commanded distance | 100 mm |
| Odom-reported distance | 119.3 mm |
| Physical tape measurement | 120 mm |
| Action reported `done` at | 102.6 mm commanded-frame |
| Odom vs physical error | 0.7 mm over 120 mm (~0.6%) |
| Lateral (Y) drift | 0.25 mm |
| Heading drift | 0.088° |

### Interpretation

**Odom accuracy:** 0.7 mm over 120 mm is within measurement noise of a
hand tape. The `wheel_radius = 0.0325 m` URDF value (commit `1952f6a`)
is validated against reality at this speed — no recalibration needed.

**Why the action reported done early (102.6 mm):** `drive_on_heading`
uses the commanded-frame displacement integral, not the odom integral.
The action considers itself done when it has *commanded* 100 mm worth
of motion, then yields back to the BT. By that moment, the robot has
actually traveled further due to coast-on.

**Coast-on:** 17 mm total between action-done and final rest. Breakdown:

- **~14 mm mechanical inertia** — the robot keeps rolling after the
  motor commands go to zero because of geartrain momentum and wheel
  inertia. This is not tunable in software; it is a physical property
  of the 30:1 gearbox + wheel mass at this speed.
- **~2.5 mm velocity_smoother ramp-down** — the
  `velocity_smoother` node interpolates between commanded velocities
  over a fixed window; the final ramp-down distance is a function of
  that window, not of `drive_on_heading`'s decel-envelope config.
- Remaining ~0.5 mm is measurement noise.

**Lateral and heading drift** are both within what you'd expect from
a differential-drive chassis at this low speed; they do not indicate
a wheel-sign or encoder issue.

### Why not Nav2 deceleration parameters

The `drive_on_heading` decel envelope parameters we attempted (commit
`fc4afff`) are only supported on Nav2 Kilted / Rolling — **not on
Jazzy** (our distro). That attempt was reverted at commit `8cf3319`.
Do not try to re-add these parameters without verifying the Jazzy API
first.

The currently-effective levers on coast-on are:

1. Lower commanded speed (already at 0.05 m/s here — going lower
   further reduces the mechanical inertia contribution but is also
   impractical for real navigation).
2. Firmware-side active counter-drive (in Phase C backlog; replaces
   the ineffective regen-brake experiment at
   [../notes/brake-attempt-forensic.md](../notes/brake-attempt-forensic.md)).
3. Tighter `velocity_smoother` window (currently minor contribution).

Counter-drive is the path being actively pursued.

## Current speed envelope

| Speed | Status |
|---|---|
| 0.05 m/s | Validated (this test) |
| ≥ 0.10 m/s | Not yet tested |
| Rotation | Not yet tested |
| Nav2 goals | Blocked on rotation test |

First rotation test is the next planned motion test (tracked in
[../project-status.md](../project-status.md) backlog).

## Related records

- Pre-wipe kinematic calibration:
  [../validation/records/2026-04-19-pre-wipe-calibration.md](../validation/records/2026-04-19-pre-wipe-calibration.md)
- Pre-Pi-rebuild DWB rotation-only diagnosis session:
  [../validation/records/2026-04-18-dwb-rotation-session.md](../validation/records/2026-04-18-dwb-rotation-session.md)
