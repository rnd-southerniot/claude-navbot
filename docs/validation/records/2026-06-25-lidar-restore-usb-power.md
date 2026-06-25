# LiDAR Restore + Pi USB Power Fix

**Date:** 2026-06-25
**Branch:** `navbot-experimental`
**Context:** Power topology changed — Pi 5 on 3S LiPo + 5V Fluree converter;
**LiDAR moved onto Pi USB power via its original USB adapter (CP2102N)**; the
RP2040 LiDAR/motor voltage dividers removed.

LiDAR came up dead after the change; debugging found **two independent root
causes**, both now fixed. LiDAR verified working: health OK, `/scan_raw`
**10.0 Hz** via the default launch.

## Root cause 1 — Pi 5 USB current cap (600 mA)

`usb_max_current_enable` was unset → Pi 5 caps **all USB ports combined at
600 mA** (the default when it can't confirm an official 5A USB-C PD supply;
here the Pi is fed from the Fluree converter). The RPLIDAR C1 (scanner +
motor) on Pi USB exceeded the budget → LiDAR couldn't start **and the RP2040
Pico was knocked off the bus** (USB-wide brownout; the CP2102N kept
re-enumerating).

**Fix:** added `usb_max_current_enable=1` to `/boot/firmware/config.txt`
(backup `config.txt.bak-20260625`) + reboot → cap lifted to ~1.6 A. Bus went
stable, Pico returned. Safe because the 5V Fluree (rated 20 A) can supply it.
`throttled` stayed `0x0` throughout (core rail fine; this was a USB-budget
issue, not undervoltage).

## Root cause 2 — LiDAR 5-pin cable TX/RX swapped

After the power fix the bus was stable but the LiDAR still returned 0 bytes at
every baud. The adapter LED was lit and it enumerated fine — so the adapter
had power; the **LiDAR's TX wasn't reaching the adapter's RX**. The 5-pin
XH2.54 cable (LiDAR ↔ adapter) had **TX/RX altered**. After the user corrected
TX/RX (manual p.11: Red=VCC, Yellow=TX, Green=RX, Black=GND), the LiDAR
responded immediately: `GET_INFO` SN `A4FFE195C1E79ED9B5E29EF120284A7C`,
`GET_HEALTH` status 0 (OK).

Note: the `cp210x ttyUSB0: failed set request 0x12 (PURGE) -110` kernel
warnings are a **benign CP2102N quirk** — they persist even with the LiDAR
working and are not the fault.

## Config 3 — stale serial_port by-id

The launch config still pointed at the old adapter
(`...CP2102..._0001...`, gone). Updated `navbot_lidar/config/sllidar_c1.yaml`
+ `lidar.launch.py` default to the current CP2102N by-id
(`...CP2102N..._f05fca3b...`). Default launch now works without an override.

## Verification

| Check | Result |
|-------|--------|
| `usb_max_current_enable` | `1` (cap lifted) |
| Pico + LiDAR on bus | both stable |
| LiDAR GET_INFO / HEALTH | SN matches, health OK |
| `/scan_raw` (default launch) | **10.0 Hz**, no errors |

## Notes / carryover

- RP2040 `lidar_v` **and** `motor_v` telemetry now read ~0 (both sense
  dividers removed) — expected; ignore those readings. `/navbot:lidar-voltage`
  is no longer meaningful.
- LiDAR on Pi USB **requires** `usb_max_current_enable=1` — do not revert it.
- 1a86 "USB Single Serial" (CH9102) device seen during debug is unrelated to
  the LiDAR.
