// SPDX-License-Identifier: MIT
#ifndef ANTICIPY_WATCHDOG_H
#define ANTICIPY_WATCHDOG_H
#include <stdbool.h>
/* E1 starts directly over SWD and has no application bootloader or OTA path.
 * Arm only after successful initialization. The main thread feeds every1s;
 * a stalled main thread resets after30s. Worker liveness is not independently
 * monitored by this watchdog and requires physical fault-injection tests.
 * A failed initialization remains accessible over SWD without reboot loops.
 */
#define WATCHDOG_TIMEOUT_MS 30000u
#define WATCHDOG_FEED_INTERVAL_MS 1000u
int watchdog_start(void);
void watchdog_feed(void);
#endif
