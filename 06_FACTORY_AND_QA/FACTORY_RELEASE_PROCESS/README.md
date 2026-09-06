# Anticipy factory-release skeleton

> **v1.0 note:** the embedded KiCad checkpoint still exposes the old Ezurio,
> Alps and JIE YI zero-copper gates so nobody can fabricate it accidentally.
> The controlled replacement order is Raytac AN54LV-15, C&K
> PTS841GMSMTRLFS, Vybronics VC0720B015F and MKDV4GCL-ABF. See
> `../03_PRODUCTION_PCB/V1_CORRECTION_ORDER.md`.

**Package state: HOLD — RFQ/DFM reference only. DO NOT FABRICATE, ASSEMBLE, PROGRAM OR SHIP.**

This directory converts the active Anticipy production concept into the control documents needed by a PCB assembler and final-assembly contractor. It does **not** turn the current concept into a released product.

## Why the hold exists

The active companion source is `../02_PRODUCTION_CAD`. It is the **v1.0 retained mechanical candidate**: the retention geometry is present and its digital fit checks pass, but it remains neither a released product drawing nor a physically qualified enclosure. It does not contain a released/routed PCB, Gerber set, drill data, IPC-356 netlist, complete orderable BOM, centroid file, paste files, panel drawing, unfiltered passing ERC/DRC reports, approved battery pack or production firmware.

The companion `../03_PRODUCTION_PCB` directory is an editable **engineering checkpoint only**. Its native KiCad structure currently passes 25 automated checks with zero structural failures, but its board is unrouted, three controlled vendor land maps remain zero-copper gates, ERC/DRC have not been run, and fabrication outputs are intentionally absent. See `PCB_RELEASE_CHECKPOINT.md`.

No supplier may infer, recreate or fabricate those missing items from the STEP placement model.

## Release states

| State | Meaning | Permitted action |
|---|---|---|
| `REFERENCE_ONLY` | Existing v0.6 mechanical, PCB-checkpoint or requirements evidence | Review, engineering and quote/DFM discussion only |
| `MISSING_BLOCKING` | Required file or approval does not exist | Stop; no fabrication or assembly |
| `DRAFT_UNRELEASED` | File exists but has not passed its gate | Internal review only |
| `RELEASED_FOR_EVT` | Signed revision and all pre-EVT gates pass | Fabricate only the stated 10-unit EVT work order |
| `RELEASED_FOR_DVT` | EVT evidence accepted and DVT ECO frozen | Fabricate only the stated 35-unit DVT work order |
| `RELEASED_FOR_PVT` | DVT evidence/compliance gates accepted | Fabricate only the stated 230-unit PVT work order |

## Contents

| File | Purpose |
|---|---|
| `FACTORY_UPLOAD_MANIFEST.csv` | Exact present/future files, hashes, recipients and release status |
| `PCB_RELEASE_CHECKPOINT.md` | Exact status and permitted use of the native KiCad engineering checkpoint |
| `PURCHASE_QUANTITIES.csv` | 10 EVT, 35 DVT and 230 PVT extended quantities |
| `PCBA_RFQ_REQUIREMENTS.md` | What the board factory must quote and confirm |
| `INCOMING_INSPECTION.md` | What Vancouver/final assembler checks before use |
| `SERIALIZED_ASSEMBLY_TRAVELER.md` | One controlled build record per serial number |
| `ASSEMBLY_TRAVELER_LOG.csv` | Machine-readable traveler event schema |
| `EOL_TEST_SPEC.md` | Every-unit end-of-line test sequence |
| `EOL_RESULTS_TEMPLATE.csv` | One electronic result row per finished unit |
| `ACCEPTANCE_AND_LOT_STOP_RULES.md` | Product gates, quarantine rules and line-stop triggers |

## Locked product requirements carried into this skeleton

- Nominal finished envelope including button membrane: **50.5 × 20.68 × 10.8 mm**; nominal body alone is 50.5 × 20.5 × 10.8 mm.
- Absolute finished envelope: **51.0 × 21.0 × 11.0 mm**.
- Finished mass: **17.4 g maximum**; the current v0.6 nominal mass budget is **12.63 g** and its 15%-reserve planning value is **14.52 g**.
- Storage: **20 continuous hours**, at a complete storage budget no greater than 5,000 bytes/s; **414 MB** required including 15% reserve.
- Battery endurance: **16 continuous hours** under the frozen sealed-unit workload.
- Controlled battery envelope: **26.0 × 12.5 × 6.0 mm maximum**, protected 1S LiPo, three wires including 10 kOhm NTC.
- Production board concept: four-layer, 0.60 mm, ENIG direction, 31.0 × 14.0 mm main region plus 6.5 × 6.5 mm RF nose.
- Structural chassis material candidate: **Covestro Makrolon 2407 polycarbonate**; exact color/lot and molding process remain held for adhesion, drop and process qualification.
- Sealed side-button candidate: C&K PTS841GMSMTRLFS, captive hard plunger and **WACKER ELASTOSIL LR 3078/50** membrane; the boot STEP is an envelope for molder DFM, not released tooling geometry.

The v0.6 CAD, retention files and fit reports listed in the upload manifest are permitted for RFQ/DFM review only. A contract manufacturer must not convert them into tooling, purchase-release authority or permission to build customer units.

Calculations are requirements, not physical passes. Acceptance requires serialized test evidence.

## Revision-control rule

Every issued work order must name one and only one PCB revision, mechanical revision, BOM revision, firmware SHA-256 and test-program SHA-256. Any change creates an ECO, increments the affected revision and forces the affected downstream tests to run again. Suppliers may not substitute a part, material, finish, adhesive, battery or process without written approval tied to an ECO.
