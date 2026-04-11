#ifndef NAVBOT_PROTOCOL_H
#define NAVBOT_PROTOCOL_H

/*
 * navbot_protocol.h
 *
 * First-pass line-based serial protocol between the Raspberry Pi ROS 2 stack
 * and the Maker Pi RP2040 base controller.
 *
 * Commands from Pi to RP2040:
 *   PING
 *   STOP
 *   RESET
 *   ESTOP
 *   CMD_VEL <linear_mps> <angular_rps>
 *   WHEEL_VEL <left_mps> <right_mps>
 *
 * Telemetry from RP2040 to Pi:
 *   ACK <command>
 *   ERR <code> <message>
 *   STATE <mode> <fault>
 *   ODOM <stamp_ms> <left_count> <right_count> <left_vel_mps> <right_vel_mps>
 *
 * Design goals:
 *   - human-readable and easy to test with a serial terminal
 *   - deterministic enough for an MVP robot
 *   - simple for Python parsing on the Pi side
 */

#define NAVBOT_PROTOCOL_BAUDRATE 115200
#define NAVBOT_PROTOCOL_MAX_LINE 96

typedef enum navbot_command_type {
    NAVBOT_CMD_UNKNOWN = 0,
    NAVBOT_CMD_PING,
    NAVBOT_CMD_STOP,
    NAVBOT_CMD_RESET,
    NAVBOT_CMD_ESTOP,
    NAVBOT_CMD_CMD_VEL,
    NAVBOT_CMD_WHEEL_VEL,
} navbot_command_type_t;

typedef struct navbot_command {
    navbot_command_type_t type;
    float value_1;
    float value_2;
} navbot_command_t;

#endif
