/* E1 battery reporting. Generic voltage percentage is development-only. */
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <zephyr/logging/log.h>
#include "battery.h"
#include "../../e1_board.h"
LOG_MODULE_REGISTER(battery,LOG_LEVEL_INF);
typedef struct
{
    uint16_t voltage;
    uint8_t percentage;
} BatteryState;

#define BATTERY_STATES_COUNT 12
/*
 * Coarse development estimate only. These generic voltage points are not a
 * pendant-specific state-of-charge calibration and must not be represented
 * as production battery accuracy.
 */
BatteryState battery_states[BATTERY_STATES_COUNT] = {
    {4200, 100},
    {4160, 99},
    {4090, 91},
    {4030, 78},
    {3890, 63},
    {3830, 53},
    {3680, 36},
    {3660, 35},
    {3480, 14},
    {3420, 11},
    {3150, 1}, // 3240
    {0000, 0}  // Below safe level
};

int battery_get_percentage(uint8_t *battery_percentage, uint16_t battery_millivolt)
{
    if (battery_percentage == NULL) {
        return -EINVAL;
    }

    // Ensure voltage is within bounds
    if (battery_millivolt >= battery_states[0].voltage) {
        *battery_percentage = 100;
        return 0;
    }
    if (battery_millivolt <=
        battery_states[BATTERY_STATES_COUNT - 1].voltage) {
        *battery_percentage = 0;
        return 0;
    }

    for (uint16_t i = 0; i < BATTERY_STATES_COUNT - 1; i++)
    {
        // Find the two points battery_millivolt is between
        if (battery_states[i].voltage >= battery_millivolt && battery_millivolt >= battery_states[i + 1].voltage)
        {
            // Linear interpolation
            *battery_percentage = battery_states[i].percentage +
                                  ((float)(battery_millivolt - battery_states[i].voltage) *
                                   ((float)(battery_states[i + 1].percentage - battery_states[i].percentage) /
                                    (float)(battery_states[i + 1].voltage - battery_states[i].voltage)));

            LOG_DBG("%d %%", *battery_percentage);
            return 0;
        }
    }
    return -ESPIPE;
}

int battery_init(void) { return 0; }
int battery_get_millivolt(uint16_t *mv) { return e1_battery_mv(mv); }
int battery_charge_stop(void) { return e1_charge_disable(); }
int battery_charge_start(void) { return -ENOTSUP; }
int battery_set_fast_charge(void) { return -ENOTSUP; }
int battery_set_slow_charge(void) { return -ENOTSUP; }
