#pragma once
#include <stdint.h>
#include <stdbool.h>
int e1_board_init(void);
int e1_mic_power(bool on);
void e1_mic_power_off_async(void);
int e1_battery_mv(uint16_t *mv);
int e1_ntc_millicelsius(int32_t *value);
int e1_charge_disable(void);
int e1_nand_probe(uint8_t id[2]);
