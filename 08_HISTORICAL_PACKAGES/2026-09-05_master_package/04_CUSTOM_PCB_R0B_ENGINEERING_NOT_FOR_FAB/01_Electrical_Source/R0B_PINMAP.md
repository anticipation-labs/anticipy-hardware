# ANT-PROD-R0B frozen pin map

Status: independent design input for schematic/PCB equivalence checks.

## U1 — Raytac MDBT50Q-1MV2

| Pins | Net / use |
|---|---|
| 1, 2, 15, 33, 55 | GND |
| 28, 30 | 3V_MAIN |
| 32 | VBUSOUT |
| 34 / 35 | USB_MCU_D- / USB_MCU_D+ |
| 16 / 19 | I2C_SDA / I2C_SCL |
| 38 / 39 | PDM_CLK / PDM_DATA |
| 42 / 44 | FLASH_SCK / FLASH_CS |
| 43 / 46 / 45 / 47 | FLASH_IO0 / IO1 / IO2 / IO3 |
| 40 / 41 | RESET / PMIC_INT |
| 48 / 49 | ACC_INT1 / ACC_INT2 |
| 24 | HAPTIC_PWM |
| 21 / 20 | UART_TX / UART_RX |
| 51 / 53 | SWDIO / SWDCLK |
| all other pins | Explicit no-connect for R0B |

## U2 — Nordic nPM1300 QEAA

| Pin | Net |
|---:|---|
| 1, 12 | 3V_MAIN |
| 2 | PVSS1 |
| 3 | SW1 |
| 4, 20, 28 | VSYS |
| 5 | SW2 |
| 6 | PVSS2 |
| 7 | PMIC_INT |
| 13 / 14 | I2C_SDA / I2C_SCL |
| 15 | SHPHLD_BTN |
| 16 / 17 | VSET2 / VSET1 |
| 18 | NTC |
| 19 | VBAT |
| 21 / 22 | VBUS / VBUSOUT |
| 23 / 24 | USB_CC1 / USB_CC2 |
| 25 / 26 | LED_BLUE_K / LED_RED_K |
| 29 | 3V_MIC |
| 30, 31 | Explicit no-connect |
| 32 | 3V_FLASH |
| exposed pad 33 | GND |

## U5 — Macronix MX35LF4GE4AD-Z4I

| Pin | Net |
|---:|---|
| 1 | FLASH_CS |
| 2 | FLASH_IO1 |
| 3 | FLASH_IO2 |
| 4 | GND |
| 5 | FLASH_IO0 |
| 6 | FLASH_SCK |
| 7 | FLASH_IO3 |
| 8 | 3V_FLASH |
| exposed pad 9 | GND |

No via or unrelated route is permitted under exposed pad 9.

## MIC1 / MIC2 — Same Sky CMM-3424DT-26165-TR

| Pin | MIC1 | MIC2 |
|---:|---|---|
| 1 | 3V_MIC | 3V_MIC |
| 2 SELECT | GND | 3V_MIC |
| 3 CLOCK | PDM_CLK | PDM_CLK |
| 4 DATA | PDM_DATA_MIC1 | PDM_DATA_MIC2 |
| 5, 6, 7, 8 | GND | GND |

R8 and R9 are 100 ohm series elements joining the two individual DATA nets to
the shared `PDM_DATA` bus at the radio. Each microphone has local 100 nF bypass.

## U3 — LIS2DW12TR

| Pin | Net |
|---:|---|
| 1 | I2C_SCL |
| 2, 9, 10 | 3V_MAIN |
| 3, 6, 7, 8 | GND |
| 4 | I2C_SDA |
| 5 | Explicit no-connect |
| 11 / 12 | ACC_INT2 / ACC_INT1 |

## Interfaces and discrete functions

- J1 USB4500 grouped lands: GND groups and four shell stakes to GND; VBUS
  groups to VBUS; A6/B6 to USB_D+; A7/B7 to USB_D-; A5/B5 to CC1/CC2;
  A8/B8 explicit no-connect.
- U4 TPD2EUSB30: pin 1 USB_D+, pin 2 USB_D-, pin 3 GND.
- R10: USB_D+ to USB_MCU_D+. R11: USB_D- to USB_MCU_D-. Both are 27 ohm.
- U6 TPD2E2U06: pin 1 USB_CC1, pin 2 USB_CC2, pin 3 GND.
- D2 ESD441: pin 1 VBUS, pin 2 GND.
- BT1 placeholder: pin 1 VBAT, pin 2 NTC, pin 3 GND. No battery MPN is approved.
- SW1: SHPHLD_BTN to GND only.
- LED1: blue and red cathodes to nPM sinks; both anodes to VSYS.
- Q1 AO3400A: gate HAPTIC_GATE, source GND, drain HAPTIC_NEG.
- D1 1N4148WS-7-F: cathode 3V_MAIN, anode HAPTIC_NEG.
- M1: 3V_MAIN to HAPTIC_NEG; 100 nF directly across motor terminals.
- NT1 joins PVSS1 to GND. NT2 joins PVSS2 to GND.
- L1 joins SW1 to 3V_MAIN. L2 joins SW2 to 3V_FLASH.
