#include "serial_parser.h"

#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static void trim_and_uppercase(const char *src, char *dst, size_t dst_size) {
    size_t start = 0;
    size_t end = strlen(src);

    while (start < end && isspace((unsigned char)src[start])) {
        start++;
    }
    while (end > start && isspace((unsigned char)src[end - 1])) {
        end--;
    }

    size_t len = end - start;
    if (len >= (dst_size - 1)) {
        len = dst_size - 1;
    }

    for (size_t i = 0; i < len; ++i) {
        dst[i] = (char)toupper((unsigned char)src[start + i]);
    }
    dst[len] = '\0';
}

const char *navbot_command_name(navbot_command_type_t type) {
    switch (type) {
        case NAVBOT_CMD_PING:      return "PING";
        case NAVBOT_CMD_STOP:      return "STOP";
        case NAVBOT_CMD_RESET:     return "RESET";
        case NAVBOT_CMD_ESTOP:     return "ESTOP";
        case NAVBOT_CMD_CMD_VEL:   return "CMD_VEL";
        case NAVBOT_CMD_WHEEL_VEL: return "WHEEL_VEL";
        default:                   return "UNKNOWN";
    }
}

const char *navbot_parse_result_name(navbot_parse_result_t result) {
    switch (result) {
        case NAVBOT_PARSE_OK:              return "OK";
        case NAVBOT_PARSE_EMPTY:           return "EMPTY";
        case NAVBOT_PARSE_UNKNOWN_COMMAND: return "UNKNOWN_COMMAND";
        case NAVBOT_PARSE_BAD_ARGUMENTS:   return "BAD_ARGUMENTS";
        default:                           return "UNKNOWN";
    }
}

navbot_parse_result_t navbot_parse_command_line(const char *line, navbot_command_t *out_command) {
    char buffer[NAVBOT_PROTOCOL_MAX_LINE];
    char extra = '\0';

    if (line == NULL || out_command == NULL) {
        return NAVBOT_PARSE_BAD_ARGUMENTS;
    }

    trim_and_uppercase(line, buffer, sizeof(buffer));
    if (buffer[0] == '\0') {
        return NAVBOT_PARSE_EMPTY;
    }

    memset(out_command, 0, sizeof(*out_command));
    out_command->type = NAVBOT_CMD_UNKNOWN;

    if (strcmp(buffer, "PING") == 0) {
        out_command->type = NAVBOT_CMD_PING;
        return NAVBOT_PARSE_OK;
    }
    if (strcmp(buffer, "STOP") == 0) {
        out_command->type = NAVBOT_CMD_STOP;
        return NAVBOT_PARSE_OK;
    }
    if (strcmp(buffer, "RESET") == 0) {
        out_command->type = NAVBOT_CMD_RESET;
        return NAVBOT_PARSE_OK;
    }
    if (strcmp(buffer, "ESTOP") == 0) {
        out_command->type = NAVBOT_CMD_ESTOP;
        return NAVBOT_PARSE_OK;
    }
    if (sscanf(buffer, "CMD_VEL %f %f %c", &out_command->value_1, &out_command->value_2, &extra) == 2) {
        if (!isfinite(out_command->value_1) || !isfinite(out_command->value_2)) {
            return NAVBOT_PARSE_BAD_ARGUMENTS;
        }
        out_command->type = NAVBOT_CMD_CMD_VEL;
        return NAVBOT_PARSE_OK;
    }
    if (sscanf(buffer, "WHEEL_VEL %f %f %c", &out_command->value_1, &out_command->value_2, &extra) == 2) {
        if (!isfinite(out_command->value_1) || !isfinite(out_command->value_2)) {
            return NAVBOT_PARSE_BAD_ARGUMENTS;
        }
        out_command->type = NAVBOT_CMD_WHEEL_VEL;
        return NAVBOT_PARSE_OK;
    }

    if (strncmp(buffer, "CMD_VEL", 7) == 0 || strncmp(buffer, "WHEEL_VEL", 9) == 0) {
        return NAVBOT_PARSE_BAD_ARGUMENTS;
    }
    return NAVBOT_PARSE_UNKNOWN_COMMAND;
}
