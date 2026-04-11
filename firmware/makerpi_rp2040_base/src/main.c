#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <math.h>

#include "hardware/pio.h"
#include "hardware/watchdog.h"
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"

#include "config.h"
#include "navbot_protocol.h"
#include "pins.h"
#include "safety.h"
#include "serial_parser.h"
#include "telemetry.h"
#include "wheel.h"

typedef enum {
    CONTROL_IDLE = 0,
    CONTROL_CMD_VEL,
    CONTROL_WHEEL_VEL,
    CONTROL_TIMEOUT,
} control_mode_t;

static wheel_t left_wheel;
static wheel_t right_wheel;
static control_mode_t control_mode = CONTROL_IDLE;

static char cmd_buf[NAVBOT_PROTOCOL_MAX_LINE];
static uint8_t cmd_len = 0;
static uint32_t last_motion_cmd_ms = 0;
static bool motion_cmd_active = false;
static uint32_t last_telem_ms = 0;

static uint32_t now_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

static void stop_all(void) {
    wheel_stop(&left_wheel);
    wheel_stop(&right_wheel);
}

static float absf_local(float value) {
    return value < 0.0f ? -value : value;
}

static void poll_encoders(void) {
    wheel_encoder_update(&left_wheel);
    wheel_encoder_update(&right_wheel);
}

static const char *mode_name(void) {
    if (safety_is_faulted()) {
        return safety_get_fault() == SAFETY_ESTOP ? "ESTOP" : "FAULT";
    }

    switch (control_mode) {
        case CONTROL_IDLE:      return "IDLE";
        case CONTROL_CMD_VEL:   return "CMD_VEL";
        case CONTROL_WHEEL_VEL: return "WHEEL_VEL";
        case CONTROL_TIMEOUT:   return "TIMEOUT";
        default:                return "UNKNOWN";
    }
}

static const char *fault_name(void) {
    if (safety_is_faulted()) {
        return safety_fault_name(safety_get_fault());
    }
    if (control_mode == CONTROL_TIMEOUT) {
        return "CMD_TIMEOUT";
    }
    return "OK";
}

static void publish_telemetry(uint32_t stamp_ms) {
    navbot_telemetry_state(mode_name(), fault_name());
    navbot_telemetry_odom(stamp_ms, &left_wheel, &right_wheel);
}

static void publish_periodic_telemetry(uint32_t stamp_ms) {
    if ((stamp_ms - last_telem_ms) >= TELEMETRY_INTERVAL_MS) {
        last_telem_ms = stamp_ms;
        publish_telemetry(stamp_ms);
    }
}

static void set_motion_active(control_mode_t mode, uint32_t stamp_ms) {
    control_mode = mode;
    last_motion_cmd_ms = stamp_ms;
    motion_cmd_active = true;
}

static void clear_motion_active(control_mode_t mode) {
    motion_cmd_active = false;
    control_mode = mode;
}

static void apply_wheel_targets_mps(float left_mps, float right_mps, control_mode_t mode, uint32_t stamp_ms) {
    wheel_set_speed_mps(&left_wheel, left_mps);
    wheel_set_speed_mps(&right_wheel, right_mps);
    set_motion_active(mode, stamp_ms);
}

static bool validate_cmd_vel(float linear_mps, float angular_rps) {
    if (!isfinite(linear_mps) || !isfinite(angular_rps)) {
        navbot_telemetry_error("BAD_ARGS", "non_finite_velocity");
        return false;
    }
    if (absf_local(linear_mps) > MAX_LINEAR_MPS || absf_local(angular_rps) > MAX_ANGULAR_RPS) {
        navbot_telemetry_error("LIMIT", "cmd_vel_out_of_range");
        return false;
    }
    return true;
}

static bool validate_wheel_targets(float left_mps, float right_mps) {
    if (!isfinite(left_mps) || !isfinite(right_mps)) {
        navbot_telemetry_error("BAD_ARGS", "non_finite_wheel_velocity");
        return false;
    }
    if (absf_local(left_mps) > MAX_WHEEL_MPS || absf_local(right_mps) > MAX_WHEEL_MPS) {
        navbot_telemetry_error("LIMIT", "wheel_velocity_out_of_range");
        return false;
    }
    return true;
}

static void handle_motion_timeout(uint32_t stamp_ms) {
    if (!motion_cmd_active) {
        return;
    }
    if ((stamp_ms - last_motion_cmd_ms) < COMMAND_TIMEOUT_MS) {
        return;
    }

    stop_all();
    clear_motion_active(CONTROL_TIMEOUT);
}

static void handle_command(const navbot_command_t *command, uint32_t stamp_ms) {
    switch (command->type) {
        case NAVBOT_CMD_PING:
            navbot_telemetry_ack_ping();
            break;

        case NAVBOT_CMD_DIAG:
            navbot_telemetry_diag(stamp_ms, &left_wheel, &right_wheel);
            break;

        case NAVBOT_CMD_STOP:
            stop_all();
            clear_motion_active(CONTROL_IDLE);
            navbot_telemetry_ack(command->type);
            break;

        case NAVBOT_CMD_RESET:
            if (!safety_reset()) {
                navbot_telemetry_error("ESTOP_HELD", "release_button_before_reset");
                break;
            }
            stop_all();
            clear_motion_active(CONTROL_IDLE);
            navbot_telemetry_ack(command->type);
            break;

        case NAVBOT_CMD_ESTOP:
            stop_all();
            clear_motion_active(CONTROL_IDLE);
            safety_set_fault(SAFETY_ESTOP);
            navbot_telemetry_ack(command->type);
            break;

        case NAVBOT_CMD_CMD_VEL: {
            if (safety_is_faulted()) {
                navbot_telemetry_error("FAULT", safety_fault_name(safety_get_fault()));
                break;
            }
            float linear_mps = command->value_1;
            float angular_rps = command->value_2;
            if (!validate_cmd_vel(linear_mps, angular_rps)) {
                break;
            }
            float half_track = WHEEL_SEPARATION_M * 0.5f;
            float left_mps = linear_mps - (angular_rps * half_track);
            float right_mps = linear_mps + (angular_rps * half_track);
            if (!validate_wheel_targets(left_mps, right_mps)) {
                break;
            }
            apply_wheel_targets_mps(left_mps, right_mps, CONTROL_CMD_VEL, stamp_ms);
            navbot_telemetry_ack(command->type);
            break;
        }

        case NAVBOT_CMD_WHEEL_VEL:
            if (safety_is_faulted()) {
                navbot_telemetry_error("FAULT", safety_fault_name(safety_get_fault()));
                break;
            }
            if (!validate_wheel_targets(command->value_1, command->value_2)) {
                break;
            }
            apply_wheel_targets_mps(command->value_1, command->value_2, CONTROL_WHEEL_VEL, stamp_ms);
            navbot_telemetry_ack(command->type);
            break;

        default:
            navbot_telemetry_error("BAD_CMD", "unsupported_command");
            break;
    }
}

static void control_step(float dt, uint32_t stamp_ms) {
    /* Encoder drain happens in the main loop and inside wheel_tick(). */

    if (safety_is_faulted()) {
        stop_all();
        clear_motion_active(CONTROL_IDLE);
        safety_tick(stamp_ms, false);
        publish_periodic_telemetry(stamp_ms);
        return;
    }

    handle_motion_timeout(stamp_ms);
    bool left_stall = wheel_tick(&left_wheel, dt);
    bool right_stall = wheel_tick(&right_wheel, dt);

    if (left_stall || right_stall) {
        stop_all();
        clear_motion_active(CONTROL_IDLE);
        safety_set_fault(SAFETY_STALL);
    }

    safety_tick(stamp_ms, wheel_is_active(&left_wheel) || wheel_is_active(&right_wheel));

    publish_periodic_telemetry(stamp_ms);
}

int main(void) {
    stdio_init_all();
    setvbuf(stdout, NULL, _IONBF, 0);

    safety_init();
    watchdog_enable(200, true);

    uint sm_left = pio_claim_unused_sm(pio1, true);
    uint sm_right = pio_claim_unused_sm(pio1, true);

    wheel_init(
        &left_wheel,
        "left",
        PIN_LEFT_FWD,
        PIN_LEFT_REV,
        pio1,
        sm_left,
        PIN_LEFT_ENC_A,
        LEFT_CPR_DEFAULT,
        LEFT_WHEEL_RADIUS_M,
        LEFT_WHEEL_SWAP_DIR
    );

    wheel_init(
        &right_wheel,
        "right",
        PIN_RIGHT_FWD,
        PIN_RIGHT_REV,
        pio1,
        sm_right,
        PIN_RIGHT_ENC_A,
        RIGHT_CPR_DEFAULT,
        RIGHT_WHEEL_RADIUS_M,
        RIGHT_WHEEL_SWAP_DIR
    );

    last_telem_ms = now_ms();
    publish_telemetry(last_telem_ms);

    uint64_t last_control_us = time_us_64();

    for (;;) {
        watchdog_update();
        poll_encoders();

        if (!stdio_usb_connected() && motion_cmd_active) {
            stop_all();
            clear_motion_active(CONTROL_IDLE);
        }

        uint64_t current_us = time_us_64();
        if ((current_us - last_control_us) >= CONTROL_LOOP_PERIOD_US) {
            uint64_t elapsed_us = current_us - last_control_us;
            last_control_us = current_us;
            control_step((float)elapsed_us / 1000000.0f, now_ms());
        }

        int c = getchar_timeout_us(0);
        if (c == PICO_ERROR_TIMEOUT) {
            tight_loop_contents();
            continue;
        }

        if (c == '\r') {
            continue;
        }

        if (c == '\n') {
            navbot_command_t command;
            navbot_parse_result_t parse_result;

            cmd_buf[cmd_len] = '\0';
            parse_result = navbot_parse_command_line(cmd_buf, &command);
            cmd_len = 0;

            if (parse_result == NAVBOT_PARSE_EMPTY) {
                continue;
            }
            if (parse_result != NAVBOT_PARSE_OK) {
                navbot_telemetry_error(navbot_parse_result_name(parse_result), "invalid_command_line");
                continue;
            }

            handle_command(&command, now_ms());
            continue;
        }

        if (cmd_len >= (NAVBOT_PROTOCOL_MAX_LINE - 1)) {
            cmd_len = 0;
            navbot_telemetry_error("LINE_TOO_LONG", "input_buffer_overflow");
            continue;
        }

        cmd_buf[cmd_len++] = (char)c;
    }
}
