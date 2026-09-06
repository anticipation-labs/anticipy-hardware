# 06 — Factory and QA

**The process is defined. It has never been executed.** No unit has been built to it, because no
board has been fabricated.

This material came almost entirely from the 2026-08-28 Execution package and exists nowhere else.
It is the strongest work in the whole hardware record — and it would have been lost if the newer
"master package" had been treated as the complete archive.

## Layout

| Folder | Contents |
|---|---|
| `FACTORY_RELEASE_PROCESS/` | EOL test spec, incoming inspection, PCBA RFQ requirements, acceptance and lot-stop rules, serialized assembly traveler, release authorization template, factory upload manifest, PCB release checkpoint, `validate_factory_release.py` |
| `QA_FIXTURES/` | 42 STL and 45 STEP fixtures, 26 drop orientations, 59 acceptance checks |
| `TEST_EVIDENCE/` | Reports from the digital verification runs, plus `physical_capture/` |

## What "verified" means here — read carefully

Execution v1.0 recorded `10/10 package checks passed`. Every one of those is a **digital** check:

```
PASS | production mechanical checks   | 23/23 pass
PASS | PLAUD-size envelope            | 50.5 x 20.68 x 10.8 mm
PASS | 20-hour storage math           | 414 MB required; 481 MB usable candidate
PASS | print-now digital validation   | 27/27 pass
PASS | PCB fabrication hold preserved | segments=0, vias=0, zones=0
PASS | no misleading Gerbers          | none
```

Its own closing line is the honest one:

> These are digital/package checks. Physical audio, RF, battery, thermal, drop, rattle,
> sweat/ingress and customer-safety tests have not happened.

Two caveats worth restating:

1. The mechanical passes were run against the **50.5 × 20.68 × 10.8 mm** envelope. The current R1
   brief specifies **56.0 × 23.0 × 12.0 mm**. If R1 is the real target, these results are stale.
2. The storage and runtime numbers are arithmetic, not measurement.

## The only physical evidence in this repository

`TEST_EVIDENCE/physical_capture/2026-07-20_pendant_audio.wav` — an audio capture from a real
pendant. Which unit and which firmware produced it is not recorded. It should be logged against a
specific build.

Beyond that file and the five BLE logs in `../05_FIRMWARE/DEVICE_RECOVERY/`, nothing in this
repository is the output of a physical test.

## The production ladder

From the Execution package's decision card — the sequence that is not worth shortcutting:

1. Print one shell and prove fit
2. Assemble one lab recorder and prove the complete data path
3. Finish and rule-check the custom PCB
4. Assemble **three** EVT units
5. Run the included tests
6. Fix what is found
7. Build 10, then 35, then the sellable lot

> Skipping step 4 does not make the schedule faster. It turns 50 boards into one expensive
> experiment.
