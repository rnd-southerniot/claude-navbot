#include "telemetry.h"

#include <stdio.h>
#include <string.h>

#include "serial_parser.h"
#include "wheel.h"

void navbot_telemetry_send(const char *payload) {
    size_t len = strlen(payload);
    uint8_t csum = navbot_checksum_xor(payload, len);
    printf("%s*%02X\n", payload, csum);
}

void navbot_telemetry_ack(navbot_command_type_t command_type) {
    char buf[NAVBOT_PROTOCOL_MAX_LINE];
    snprintf(buf, sizeof(buf), "ACK %s", navbot_command_name(command_type));
    navbot_telemetry_send(buf);
}

void navbot_telemetry_ack_ping(void) {
    char buf[NAVBOT_PROTOCOL_MAX_LINE];
    snprintf(buf, sizeof(buf), "ACK PING %s", FIRMWARE_VERSION);
    navbot_telemetry_send(buf);
}

void navbot_telemetry_error(const char *code, const char *message) {
    char buf[NAVBOT_PROTOCOL_MAX_LINE];
    snprintf(buf, sizeof(buf), "ERR %s %s", code, message);
    navbot_telemetry_send(buf);
}

void navbot_telemetry_state(const char *mode, const char *fault) {
    char buf[NAVBOT_PROTOCOL_MAX_LINE];
    snprintf(buf, sizeof(buf), "STATE %s %s", mode, fault);
    navbot_telemetry_send(buf);
}

void navbot_telemetry_odom(uint32_t stamp_ms, const wheel_t *left, const wheel_t *right) {
    char buf[NAVBOT_PROTOCOL_MAX_LINE];
    snprintf(
        buf, sizeof(buf),
        "ODOM %lu %lld %lld %.4f %.4f",
        (unsigned long)stamp_ms,
        (long long)left->enc_count,
        (long long)right->enc_count,
        (double)wheel_cps_to_mps(left, left->speed_filtered),
        (double)wheel_cps_to_mps(right, right->speed_filtered)
    );
    navbot_telemetry_send(buf);
}

void navbot_telemetry_diag(uint32_t stamp_ms, const wheel_t *left, const wheel_t *right) {
    char buf[NAVBOT_PROTOCOL_MAX_LINE];
    snprintf(
        buf, sizeof(buf),
        "DIAG %lu L:%d,%.1f,%.1f,%.1f,%.1f,%.1f,%lu R:%d,%.1f,%.1f,%.1f,%.1f,%.1f,%lu",
        (unsigned long)stamp_ms,
        (int)left->duty,
        (double)left->speed_setpoint_cps,
        (double)left->speed_filtered,
        (double)left->speed_pid.last_p_term,
        (double)left->speed_pid.last_i_term,
        (double)left->speed_pid.last_d_term,
        (unsigned long)left->stall_timer_ms,
        (int)right->duty,
        (double)right->speed_setpoint_cps,
        (double)right->speed_filtered,
        (double)right->speed_pid.last_p_term,
        (double)right->speed_pid.last_i_term,
        (double)right->speed_pid.last_d_term,
        (unsigned long)right->stall_timer_ms
    );
    navbot_telemetry_send(buf);
}
