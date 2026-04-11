#include "telemetry.h"

#include <stdio.h>

#include "serial_parser.h"
#include "wheel.h"

void navbot_telemetry_ack(navbot_command_type_t command_type) {
    printf("ACK %s\n", navbot_command_name(command_type));
}

void navbot_telemetry_error(const char *code, const char *message) {
    printf("ERR %s %s\n", code, message);
}

void navbot_telemetry_state(const char *mode, const char *fault) {
    printf("STATE %s %s\n", mode, fault);
}

void navbot_telemetry_odom(uint32_t stamp_ms, const wheel_t *left, const wheel_t *right) {
    printf(
        "ODOM %lu %ld %ld %.4f %.4f\n",
        (unsigned long)stamp_ms,
        (long)left->enc_count,
        (long)right->enc_count,
        (double)wheel_cps_to_mps(left, left->speed_filtered),
        (double)wheel_cps_to_mps(right, right->speed_filtered)
    );
}
