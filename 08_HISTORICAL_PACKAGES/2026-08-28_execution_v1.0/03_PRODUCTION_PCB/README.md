# Anticipy EVT-A KiCad design checkpoint

> **v1.0 stop sign:** this editable checkpoint is the electrical starting point,
> not the final v1.0 board. Its placed U1/U4/SW1/M1 candidates are superseded by
> Raytac AN54LV-15, MK Founder MKDV4GCL-ABF, C&K PTS841GMSMTRLFS and
> Vybronics VC0720B015F. It also contains a DRV2605L A2/REG net-label error.
> Read `V1_CORRECTION_ORDER.md` before editing. Gerbers made from the present
> files would be wrong and must not be ordered.

This directory is the most complete **honest** production-PCB checkpoint that can be made from the currently controlled information. It is an editable native KiCad project with a connected, named schematic architecture; an exact-size four-layer board; verified custom footprints for the parts whose manufacturer drawings are public; a corrected haptic-motor scallop; test points; a source-linked BOM; and a deterministic verifier.

It is **not a fabrication release**. Gerbers are intentionally absent. The Ezurio radio module, Alps button and JYC720FDRL motor-FPC landing zone have zero-copper placeholders because their controlled land maps are unavailable; inventing those pads would make a dangerous fake “finished” board.

## Open this first

- `anticipy_evt_a.kicad_pro` — native KiCad project
- `anticipy_evt_a.kicad_sch` — electrically named architecture schematic
- `anticipy_evt_a.kicad_pcb` — exact-size placement/footprint checkpoint
- `bom/EVT_A_BOM.csv` — order-code and verification status
- `docs/OPEN_ITEMS.md` — shortest path from checkpoint to three EVT boards
- `reports/STRUCTURAL_VERIFY.txt` — actual automated results
- `reports/PAD_NET_MAP.csv` — every board pad and its named net

## What is complete

| Item | Result |
|---|---|
| Board construction | Four copper layers, 0.60 mm nominal |
| Board bounds | 37.50 × 14.00 mm overall |
| Main region | 31.00 × 14.00 mm |
| RF nose | 6.50 × 6.50 mm |
| Haptic clearance | Corrected 4.10 mm-radius concave scallop at the rigid motor pocket |
| Named electrical nets | 55, covering charge, battery, PMIC, storage, audio, haptic, RF, button and debug |
| Verified custom footprints | nPM1300-CAAA, W25N04KVZEIR, DRV2605LYZFR, IM69D128S, Johanson antenna |
| Microphone ports | Two manufacturer-sized 0.60 mm PCB acoustic holes |
| Bring-up access | Ground, charge, battery, rails, flash, microphones, haptic and debug test pads |
| Placement checks | Eight 15%-expanded subsystem reserves and all 81 actual placed courtyards fit without same-side overlap |
| Schematic coverage | All 47 non-test board references appear in the connected schematic |
| Structural verifier | 25 passes, zero structural failures |

## Two design corrections made here

1. **Use the 3.0 V buck rail for the digital system.** The W25N04KV NAND cannot be treated as a 1.8 V device. The optional 1.8 V rail remains separate; the two buck outputs are never tied together.
2. **Use Samsung CIGT201610EH2R2MNE for L1/L2.** It is the exact 2.2 µH inductor in Nordic’s nPM1300-CAAA Config 4 reference BOM. The previously proposed Murata part has a 425 mΩ maximum DCR, which exceeds Nordic’s stated 400 mΩ ceiling.

## Deliberate release gates

| Gate | Why it is held | Exact next action |
|---|---|---|
| U1 Ezurio 453-00224R | Official symbol, footprint and pin map require Ezurio account access | Download the official Altium/DXF symbol/footprint, datasheet and development-kit schematic; import and independently cross-check every pad |
| SW1 Alps SKSCLCE010 | Side-push body/orientation is verified, but the formal delivery drawing remains members-only | Obtain the controlled product drawing and replace the zero-pad side-switch envelope |
| J3 / M1 JYC720FDRL | The selected motor is a 7 × 2 mm FPC ERM intended for hot-bar attachment, but the controlled FPC land/process drawing is not public | Obtain the supplier drawing and approved hot-bar profile; replace the zero-pad J3 landing-zone gate and qualify weld pull/strain relief |
| Battery | `BAT-ANT-200-001` is only a controlled envelope | Approve supplier drawing, polarity, protection, 10 kΩ NTC and safety/transport documents |
| Passives/LED | Several exact values are known, but orderable MPNs/derating are not all frozen | Select order codes against the final stack-up, temperature and availability |
| Routing | U1 pad map is unavailable | Import U1 first, then route power/RF/audio/storage and run review |
| RF | Evaluation match values are not final product values | Tune the closed, populated pendant on a VNA |
| CAD | The earlier straight-edge PCB STEP does not contain the retained motor scallop | Re-export the controlled candidate outline and re-run full assembly interference/Z-stack checks |

## Verification commands

```bash
python tools/generate_release.py
python tools/verify_release.py
```

The included verifier parses the native S-expressions independently and checks geometry, nets, pad maps and release gates. It is **not** KiCad ERC/DRC. `kicad-cli` was not installed in this runtime, so `reports/ERC_NOT_RUN.txt` and `reports/DRC_NOT_RUN.txt` state that plainly.

After the two vendor files are imported and routing is complete, run unfiltered KiCad ERC/DRC and the selected assembler’s DFM. Only then generate fabrication outputs for **three EVT boards**, not customer production.
