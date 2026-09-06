# Safe first-board bring-up

This procedure begins only after the release gates, routing, ERC/DRC and assembly DFM are complete.

1. Inspect the unpowered board under magnification. Confirm U1/U4/U5/U6 orientation, solder bridges, antenna keep-out, microphone holes and charge/battery polarity.
2. Keep the pouch battery and motor disconnected.
3. Inject the approved system input through a current-limited bench supply with a conservative current limit. Watch for immediate overcurrent or heating.
4. Measure `VSYS`, `3V0` and `1V8` at their test pads. Confirm the buck outputs are separate.
5. Verify SWD/reset/UART access and radio identity before enabling high-rate peripherals.
6. Verify NAND ID, erase/program/read, ECC status and bad-block table using isolated flash access.
7. Power and validate each microphone separately, then together. Measure noise with PMIC idle and switching.
8. Connect a sacrificial measured ERM load or current probe before the real motor. Configure DRV2605L for the measured motor, then test short events.
9. Validate charge input with the exact puck and thermistor simulation before connecting a cell.
10. Connect an approved protected cell last. Verify charge current, NTC cutoffs, termination, ship mode, brown-out shutdown and temperature.

Any unexpected rail, current, heat, storage corruption or RF/acoustic problem stops the test. Only three EVT boards should be exposed to this process before the design is revised.

