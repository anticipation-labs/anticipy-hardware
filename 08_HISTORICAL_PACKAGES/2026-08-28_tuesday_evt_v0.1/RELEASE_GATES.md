# Release gates

## Current status

| Gate | Status |
|---|---|
| Nominal CAD inside +10% size ceiling | PASS |
| Frame and face meshes watertight | PASS |
| Firmware cleanly compiles to UF2 | PASS |
| Real component fit | NOT TESTED |
| Real microphone and decoded audio | NOT TESTED |
| Real microSD record/reboot/backfill | NOT TESTED |
| Real iPhone live and backlog transfer | NOT TESTED |
| Closed-shell Bluetooth range | NOT TESTED |
| Safe charge temperature/current | NOT TESTED |
| 16-hour runtime | NOT TESTED |
| Encryption of stored audio | FAIL — NOT IMPLEMENTED |
| Drop and chain pull | NOT TESTED |

## A unit may leave the bench only after

1. Ten cold boots succeed.
2. Sixty minutes of live audio decodes without unexplained gaps.
3. One hour offline records and backfills after reconnect.
4. One hundred button presses and haptic pulses cause no reset.
5. Charging causes no abnormal cell or enclosure heating.
6. Closed-shell Bluetooth works at the agreed range.
7. The chain hole passes a controlled pull test and the unit passes a one-metre drop test.

Do not promise 16 hours until one sealed unit actually runs for 16 hours. Do not record customer conversations until stored audio is encrypted and the privacy/security gates in the firmware folder pass.
