# Architecture decision

## Build for Unit 001

Use:

- black PETG body and hooked face printed from the supplied exact historical
  STL files (or the ordered nylon pieces if they later arrive);
- 4.50 mm printed mid-band and shelf-seated battery bridge;
- XIAO nRF52840 Sense;
- a documented protected 1S pack that passes either the primary
  25 x 10 x 5.5 mm gauge or the named conditional DTP401525
  25.3 x 15 x 4.0 mm gauge and all matching release gates;
- ordered Vybronics VCLP1020B002L motor, no larger than its
  10.2 mm diameter x 2.3 mm tolerance envelope;
- ordered AO3400A / 1N4148W-HF / 100 ohm / 100 kohm SMD haptic driver inside
  the finished 8 x 4 x 2 mm island;
- fully insulated SMD driver island no larger than 8 x 4 x 2 mm;
- live BLE audio to the Anticipy iPhone app;
- no microSD daughterboard.

The strongest documented battery target is Renata ICP501022UPM: 80 mAh,
24 x 10 x 5.5 mm maximum, safety circuit, 40 mA normal/80 mA maximum charge.
Its manufacturer datasheet states IEC 62133 certification and the matching
UN38.3 summary reports T1-T8 passed. Local stock must still be confirmed.

### No-adhesive closure for the Renata target

If qualified 24 x 10 x 5.5 mm Renata hardware is selected, a separate
support-free screw-retained band is available. Two keyed PETG posts clamp the
band to the body with M2 x 10 mm flat countersunk screws through the back; the
hooked face remains removable. Its dedicated exact audit
qualifies a mechanical motor envelope up to 10.2 mm diameter x 2.7 mm at the
existing centre. Use only the named closure parts, motor gauge and procedure
in `PRIMARY_RENATA_ONLY_SCREW_RETENTION.md`.

This screw layout is not compatible with the wide-cell Plan B or the barrel
motor. The exact audit intentionally reports a 32.28 mm3 post/rotated-driver
collision and aborts if that incompatibility disappears.

## Conditional wide-cell Plan B

SparkFun PRT-13853 references the protected Data Power DTP401525, 110 mAh.
Its datasheet gives a 25 x 15 x 4.0 mm cell maximum and a 25.3 mm L2 maximum;
the conservative CAD gauge uses **25.3 x 15 x 4.0 mm**. The exact historical
shell audit passes with the current band and bridge when the driver is rotated
to 4 x 8 x 2 mm between the cell and motor. Nominal clearance is only 0.15 mm
under the historical shelf and 0.40 mm between adjacent hard parts, and the
cell overlaps the complete conservative antenna zone.

This is a fit candidate, not a shipping authorization. Obtain the exact
received label/lot, matching manufacturer datasheet, protection details,
polarity and matching UN38.3 summary; gauge the pack including PCM, wrap,
seams and folded tabs; then pass witness-film closure and closed-shell RF,
charge and thermal tests. Lee PID8834 is a separate local listing and is not
proved equivalent to PRT-13853/DTP401525.

## Why no microSD

The Adafruit microSD BFF adds about 3 mm before solder tolerance. Keeping it
would require a visibly thicker band, more wiring, another failure surface,
and storage firmware validation. The iPhone app already supplies the actual
recording path. Unit 001 is configured as a paired-phone live-stream device
and may be handed off only after the release record passes.

The XIAO has 2 MiB onboard QSPI, but a short-cache firmware profile remains a
development artifact until encrypted-at-rest storage, owner-only access,
durable phone ACK, power-cut recovery, and loss telemetry all pass.

## Fallbacks

- If the ordered Vybronics motor is not physically delivered, Lee PID10431 is
  a delivery fallback only. Its listed 10.0 x 2.7 mm body is inside the
  Renata screw-layout's mechanically qualified 10.2 x 2.7 mm envelope, but the
  received motor must pass that gauge and still requires its own identity,
  current, duty, driver-margin, no-reset, thermal, audio, haptic and RF tests;
  it does not inherit the Vybronics electrical release. The barrel envelope
  remains a measurement reference only because this packet has no qualified
  rotor guard.
- If no battery passes documentation and fit, do not install a donor or raw RC
  cell. Use a documented cell in a larger printed enclosure for that unit.
- If haptic causes reset, buzz, battery contact, or RF failure, remove it and
  disclose the missing function; phone haptics are not pendant haptics.

## Release language

Describe a passed Unit 001 as a **functional investor sample in the final
industrial-design direction**. Do not call it production-validated,
certified, waterproof, or customer-sale-ready until those programs exist.
