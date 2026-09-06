# ⛔ START AT BUILD_BOOK.html (v5.1, 2026-08-19)

The July v3/v4 instructions below are SUPERSEDED. v4 shipped with a battery-seat
defect (bay 0.9mm short — fixed in v5). Print PRINT_ME_v5_3pendants.3mf in BLACK ABS
(not PLA — see build book §02). Full program: BUILD_BOOK.html or
https://claude.ai/code/artifact/a4fd3274-2a77-4416-9cda-978fbb8d097d

## v5.1 (2026-08-19) — after the Devin-night P2S print

Same shells, three additions (geometry of the six plate halves provably
unchanged — volume-identical re-export):

1. **COUPON_FIRST.3mf — print this before the plate, same filament+profile.**
   Four slices of the real click joint: 1 tongue + grooves at 0.16/0.22/0.28mm
   (notch count = which). Snuggest one that clicks home by hand = this
   printer's clearance. 0.16 → print the plate as-is; otherwise regenerate
   halves with `-D LIP_CLR_OVERRIDE=<value>` and rerun make_3mf_v5.py.
2. **BATTERY=200 preset** (`-D BATTERY=200`): 33.4 × 63.1 × 12.6 tag for a
   502025-class 200mAh cell. stl_v5/v5_bat200_front|back.stl are exported —
   but MEASURE the actual cell and set BAT200_W/L/T before trusting them.
3. **Machine gate extended: 83/83 pass** (V1–V4 × storage × 5 fit-proofs ×
   both batteries + jointgap at all three coupon clearances). Gate script
   pattern: every `HALF="test_*"` export must come back EMPTY.

---

# Anticipy Pendant Shell v3 — Print & Assembly Guide

Pill-shaped two-half glued FDM shell for the XIAO nRF52840 (Sense) + BLL 752042
500 mAh LiPo, styled after the anticipy.ai production pendant (stadium pill,
top bail hole, countersunk front dot, debossed back wordmark, flush USB-C).

Everything below survived two rounds of adversarial design review plus
machine-checked fit tests (`HALF="test_*"` modes export EMPTY meshes for all
four variants — meaning battery, board and USB nose provably fit, and chain
and dowels provably never touch the electronics).

## Variants — print all 8 halves on one plate

| Variant | Files | Assumes | W×H×D (mm) | Role |
|---|---|---|---|---|
| **V1 FIT** | `anticipy_v1_*` | pins clipped flush | 26.5 × 61.2 × 23.8 | **primary** |
| V2 ROOMY | `anticipy_v2_*` | pins clipped | 27.2 × 61.6 × 25.4 | if V1 tight |
| V3 NOCUT | `anticipy_v3_*` | pins untouched | 26.5 × 61.2 × 30.8 | refuse-to-clip insurance |
| V4 FIT-LOOSE | `anticipy_v4_*` | pins clipped | 26.5 × 61.2 × 23.8 | looser holes/dowels |

Size floor, for reference: the battery alone is 43 × 20.5 × 8 mm and the
compressed electronics stack is ~18 mm deep — V1 is within ~2.3 mm of the
theoretical minimum in every axis.

## Design features

- **Bail**: Ø6.4 through-hole at the top, chamfered both sides. Thread the
  3 mm chain directly, or (nicer, like the site) use a **10–12 mm stainless
  jump ring**. A metal jump ring also stops long-term chain wear on PLA.
- **USB-C**: flush port in the bottom — the receptacle's metal face sits
  flush with the shell, exactly like production hardware. Any compliant
  cable seats fully (0.45 mm landing facet is built in). The port hole also
  registers the board during assembly.
- **Mic/status dot**: countersunk Ø1.8 hole on the front, at the mic's true
  location from Seeed's CAD. Doubles as the enclosure vent — never seal it.
- **Wordmark**: "Anticipy" debossed 0.6 mm on the back, reads top-to-bottom.
  Verified present in the mesh (57 mm² of letter floors at exact depth).

## Filament

**Bambu PLA Metal — Iron Gray Metallic (13100)**: closest brushed-titanium
look, zero metal filler (RF-transparent for BLE), best impact toughness of
Bambu's PLA/PETG/ASA lineup per their own TDS, skin-safe.
Never use carbon-fiber or metal-filled filament (kills the antenna).

## Print settings (Bambu Studio; X1C/P1S/A1; 0.4 mm nozzle)

- All 8 STLs **as exported, flat face down** on textured PEI. No supports.
- 0.12 mm Fine base profile, then per object: **variable layer height**
  (0.08–0.16, smooth), **5 walls**, 5 top/bottom layers, 12 % gyroid,
  **ironing: top surfaces**, seam: scarf/aligned-rear.
- Elephant foot compensation 0.15 mm (keeps the glue rim square).
- Expect ≈ 3–3.5 h total, ~100 g. Fits a 256×256 plate easily (2×4 with
  gaps); on a 180×180 A1 mini use two plates of 4.

## Parts to have ready

- Flush cutters, kapton or electrical tape
- **3 mm open-cell PU foam** pad ~20 × 40 (a strip of soft packing foam works)
- Small piece of **1 mm VHB / double-sided tape**
- Two **5.5 mm pieces of 1.75 mm filament** (the alignment dowels)
- Medium/gel CA (Loctite Gel Control) or 5-min epoxy; a USB-C cable you
  don't love (glue-up jig); PTFE tape or candle wax for its nose

## Assembly — rehearse dry FIRST, then glue (15 min)

1. **Clip the header pins flush** at the insulators, both rows (V1/2/4).
   Glasses on — pins fly. Kapton over the stubs. (V3 = skip clipping.)
2. **Tack the two filament dowels** into the BACK half's holes with a dot of
   CA. They stand proud ~2.5 mm.
3. **Dress the wires dry**: fold so the upper-pad wire takes a 2 mm sideways
   jog and NEVER crosses the other wire — crossed wires are the one thing
   that can hold the halves apart. Kapton-tape the fold to the battery.
4. **Mount the battery** into the BACK half bay, wire-end down, on a strip of
   VHB. Lay the 3 mm foam pad on its face.
5. **Seat the board** in the FRONT half — **nose-first at a slight tilt**
   (~15°, USB nose leading into the port hole, then lay the board flat; a
   flat drop doesn't clear the hole roof — the tilt is mandatory and easy).
   Push until the PCB edge lands on the internal shelf. Wedge a small
   3×3×18 mm foam strip behind the board's far edge as a backstop.
   Sanity check while it's visible: RST button appears to the RIGHT of
   the USB port, LEDs to the LEFT — if reversed, stop (wrong orientation).
   Extra registration trick: slide a waxed 6 mm rod (drill-bit shank) through
   both halves' bail holes during glue-up — a third alignment point for free.
6. **Dry-close** the halves over the wires, dowels engaging first, and check
   the seam pulls fully flush. Open, fix any wire that got pinched.
7. **Wax/PTFE the jig cable's nose**, plug it through the port into the
   board from outside. Glue: thin continuous CA bead on the BACK half's rim
   only. Close, press 60 s, rubber-band. Wiggle the jig plug at 2 min so it
   can't bond. Cure 1 h; pull the jig; thread chain/jump ring.

## After-print finishing (the CNC look)

- 400 → 800 wet-sand the seam, then a light one-direction 800-grit pass over
  everything (long axis) — fakes brushed metal convincingly on Iron Gray.
- No acetone, no heat.

## Recovery / ops notes

- The glued shell removes RST access forever. Fine: 1200-baud USB touch and
  BLE DFU recovery are proven (see `~/anticipy-pendant-restore/`), and the
  USB port stays exposed.
- LiPo rules: hot cars kill the battery before the shell; the mic hole is
  the vent.

## Regenerate / tweak

```bash
openscad --backend=manifold -o out.stl --export-format=binstl \
  -D VARIANT=1 -D 'HALF="front"' pendant.scad
```
Fit-proof any change: `HALF="test_batfit"|"test_brdfit"|"test_bailclear"|"test_dowelclear"`
must all export empty meshes for the variant you touched.
