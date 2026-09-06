# Anticipy indicator behavior

The board uses one very small low-current red/blue LED. Its two cathodes are
driven by the nPM1300 LED current sinks; its anodes connect to VSYS.

| State | Light behavior |
|---|---|
| Powered but idle | Off |
| Recording | Slow blue pulse every 3 seconds |
| Bluetooth pairing | Alternating blue/red, 1 Hz |
| Bluetooth connected | Two short blue flashes, then off |
| Charging | Dim red pulse |
| Charged | One blue flash when cable is inserted, then off |
| Battery below 10% | Two red flashes every 60 seconds |
| Storage/microphone failure | Three red flashes after button press |
| Firmware update | Alternating blue/red, 2 Hz |

The LED should not remain brightly lit during normal recording. This preserves
battery life and makes the pendant less distracting. Firmware should cap LED
current to the lowest level that remains visible through the final light pipe.
