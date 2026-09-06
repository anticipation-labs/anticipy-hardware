# Size audit

## Hard reference

PLAUD NotePin S official hardware envelope: **51 × 21 × 11 mm**. Official mass: **17.4 g without the magnetic pin**. These are hard maximums for this project, not nominal manufacturing targets. [Official PLAUD NotePin S](https://www.plaud.ai/pages/plaud-notepin-s)

## Devin design versus the hard reference

| Axis | Hard maximum | Devin | Absolute excess | Percentage excess |
|---|---:|---:|---:|---:|
| length | 51 mm | 58 mm | 7 mm | 13.725% |
| width | 21 mm | 24 mm | 3 mm | 14.286% |
| thickness | 11 mm | 12.6 mm | 1.6 mm | 14.545% |

Rectangular-envelope comparison:

```text
PLAUD box = 51 × 21 × 11       = 11,781.0 mm³
Devin box = 58 × 24 × 12.6     = 17,539.2 mm³
Excess    = 17,539.2/11,781 − 1 = 48.877%
```

Devin's “15% margin” was added outside the product maximum. That creates a larger product; it does not fit a design safely inside the maximum.

## v0.4 founder pilot

The no-custom-PCB pilot is intentionally **76 × 33 × 17 mm**:

| Axis | Excess over PLAUD |
|---|---:|
| length | 25 mm / 49.020% |
| width | 12 mm / 57.143% |
| thickness | 6 mm / 54.545% |
| rectangular envelope | 261.905% larger |

This size is the honest cost of stacking ready-made XIAO and XTSD boards, hand wires, connectors, a 500 mAh protected cell and assembly room.

## v0.6 production nominal

The retained body is **50.5 × 20.5 × 10.8 mm**. The finished nominal including the 0.18 mm side button membrane is **50.5 × 20.68 × 10.8 mm**.

| Axis | Nominal headroom | Headroom after +0.15 mm finished tolerance |
|---|---:|---:|
| length | 0.50 mm | 0.35 mm |
| width | 0.50 mm | 0.35 mm |
| thickness | 0.20 mm | 0.05 mm |

Its rectangular envelope is 11,180.7 mm³, **5.095% smaller** than the PLAUD box. The small 0.05 mm residual thickness headroom makes supplier process capability and measured samples mandatory before release.

## Why removing XIAO pins does not solve it

Removing header pins removes unwanted height and weight. It does not change the XIAO board's 21 × 17.8 mm outline, and the XTSD is another 21.5 × 17.7 × 2.9 mm board. The wiring, battery, motor, button and shell still need room.

That is why:

- founder pilot = ready-made boards, no custom PCB, larger body;
- production body = one shaped custom PCB, smaller parts, factory assembly.
