# Anticipy mechanical retention specification

## The answer in tiny words

The enclosure is an egg carton, not an empty jewellery box. Every part gets a shaped seat that stops left/right/forward/back motion, plus a fastener, keeper or qualified adhesive that stops up/down motion.

Foam is only a controlled tolerance spring. Random foam, hot glue and shell pressure are not production retention methods.

## The six-direction rule

For every internal part, the drawing must identify what blocks movement in +X, -X, +Y, -Y, +Z and -Z. The finished CAD and worst-case tolerance stack must show that no rigid feature presses, rubs or impacts the lithium pouch.

## Frozen retention architecture

| Part | Sideways retention | Up/down retention | Production method | Release proof |
|---|---|---|---|---|
| PCB | One round datum, one slotted datum and edge stops | Three support lands, two releasable snap fingers and two 0.15 mm preload pads; retained screws are the EVT fallback | No shell-pressure-only retention and no molding undercut | No PCB shift, mic misalignment, cracked solder or new rattle after drop/vibration |
| Battery | Five-sided rounded cradle sized from the supplier's **maximum in-service** pack drawing | `tesa 77010`, 0.10 mm, custom pull-tab strip; only controlled edge compliance; swelling space remains free | Pull tab remains reachable; no hard rib, motor, foam pile or cap pressure over the pouch | Drop/vibration survivor is opened: no dent, crease, abrasion, tab strain or measured shift |
| Haptic motor | 7.30 mm starting pocket ID, 0.60 mm shelf, rigid pocket sectors and crash-stop keepers, **beside the battery** | controlled 0.05 mm PSA under the motor; keeper carries release shock | Vybronics `VC0720B015F` wired motor; route both leads in a defined channel with separate strain relief and solder pads | 50,000 haptic cycles and drop/vibration cause no debond or rattle |
| Button | Captive POM/PC plunger aligned to C&K PTS841GMSMTRLFS side-push axis | WACKER ELASTOSIL LR 3078/50 membrane and hard travel stops | The switch is never used as the enclosure seal or travel stop | 100,000 finished-assembly presses; no stick, miss, leak or double event |
| Microphones | PCB datum aligns each bottom port directly to one housing duct | `Nitto SCF400TT`, 0.15 mm, custom annular internal gasket | One `GORE GAW337` vent per housing port; controlled fixture placement | Sealed acoustic sweep, rub/wind/haptic test and ingress test |
| Battery/motor wires | Molded routing channel; no free loop | Strain-relief feature at termination | Fixed wire length or FPC; keyed connector if used | Pull and shake inspection; no wire can touch shell, mic or sharp edge |
| Aluminium/RF caps | Tongue/step registration controls flushness and shear | `3M VHB 5906`, 0.15 mm, continuous 1.1-1.2 mm die-cut perimeter ring; geometry carries impact | Controlled surface clean, alignment fixture, at least 100 kPa uniform pressure and 24 h hold before abuse testing | Seam measurement, peel/push test, temperature/sweat/drop and ingress |
| Chain eye | v0.6 internal annular boss spreads load into the rear structure | Boss geometry receives molding DFM; metal insert only if pull tests require it | Necklace includes a defined breakaway clasp | Static and cyclic pull with no crack, sharp edge or seam movement |

## Selected material families

These are engineering candidates, not permission to substitute whatever tape looks similar.

| Job | Candidate | Nominal thickness | Why |
|---|---|---:|---|
| Aluminium-to-Makrolon 2407 PC perimeter bond | `3M VHB 5906` | 0.15 mm | Thin conformable foam tape intended to bond and seal; die-cut as one unbroken ring |
| Removable battery bond | `tesa 77010 Bond & Detach` | 0.10 mm | Battery-mounting tape with shock resistance and a stretch-release service pull tab |
| PCB preload and microphone internal gaskets | `Nitto SCF400TT` | 0.15 mm | Thin closed-cell foam for controlled impact absorption and dust sealing; use only in drawing-controlled pads/rings |
| Motor bond | `3M 93005LE` | 0.05 mm | Very thin custom die-cut under the motor; it is secondary to the rigid pocket/keeper |
| External microphone vents | `GORE GAW337` | 0.36 mm; 3.0 mm OD / 1.4 mm ID | Small acoustic vent; published insertion loss is below 1.3 dB at 1 kHz |
| Button membrane | `WACKER ELASTOSIL LR 3078/50 A/B` | 0.18 mm web starting nominal | Self-adhesive 50A LSR candidate; substrate adhesion and force/leak life remain physical gates |

Primary product information:

- 3M VHB 5906: <https://www.3m.com/3M/en_US/p/d/b40065769/>
- 3M VHB application guidance: <https://www.3m.com/3M/en_US/bonding-and-assembly-us/resources/full-story/?storyid=b3996cbd-9954-455f-8e72-88e452ca38c0>
- 3M 93005LE: <https://www.3m.com/3M/en_US/p/d/b40070440/>
- tesa 77010: <https://www.tesa.com/en/industry/tesa-77010-bond-and-detach.html>
- Nitto SCF400TT: <https://www.nitto.com/us/en/products/sealing/scf002/>
- GORE GAW337 case data: <https://www.gore.com/resources/case-study-gore-acoustic-vents-small-id-size-high-quality-mass-production-gated>
- VC0720B015F manufacturer record: <https://www.vybronics.com/coin-vibration-motors/with-brushes/v-c0720b015f>
- PTS841 manufacturer record: <https://www.littelfuse.com/products/switches/tactile-switches/pts841>
- WACKER ELASTOSIL LR 3078/50: <https://www.wacker.com/h/en-us/silicone-rubber/liquid-silicone-rubber-lsr/elastosil-lr-307850-ab/p/000099151>

## Structural shell rule

The aluminium face must not be the only thing preventing the enclosure from spreading apart. The production Makrolon 2407 polycarbonate carrier supplies the structural wall, datum ledges and impact path; the aluminium cap supplies the premium surface and shares load through its full perimeter bond. PA12 is limited to bridge prototypes unless it independently passes the same tests.

Use a stepped/tongue-and-groove perimeter so impact load is transferred through geometry in shear, not peeled directly through the adhesive. Recess the aluminium edge 0.20-0.30 mm behind the polymer impact rim so a corner drop reaches tough polymer before it catches and peels the cosmetic metal. Give the VHB ring a continuous 1.1-1.2 mm land with no splice.

## Motor position is changed in v0.6

The rejected v0.4 model put the 7 mm motor above the soft battery. v0.6 puts it beside the pouch on a rigid shelf with a circular wall, two Z keepers and an FPC exit.

The controlled centers are battery `(0.1, 0.0)` and motor `(16.9, -4.8)`, with a `4.10 mm` PCB-scallop radius. Automated geometry proves 0.30 mm nominal motor-to-pouch XY separation and 0.60 mm radial board-to-can separation. Supplier maximum drawings, sample measurements and physical shock tests still control release.

Never solve the stack by squeezing the lithium pouch.

## v0.6 geometry completed; mandatory DFM/qualification before DVT

- Convert the modeled lands, snap fingers, motor keepers, chain boss and button seat into drafted, radiused, toolable molding geometry with the selected factory.
- Replace controlled envelopes with signed maximum battery, motor/FPC, switch and routed-PCBA drawings.
- Export converter tool paths for the VHB ring, pull tape, microphone rings, PCB pads and motor disc.
- Add final assembly-tool access, closure/press datums and production inspection gauges.
- Publish min/nominal/max tolerance stacks for the molded parts and every Z layer.
- Prove snap strain, battery service path, LSR adhesion/force, microphone compression, cap adhesion and chain pull on physical EVT/DVT samples.

The v0.6 files now prove retained placement without positive-volume intersections. Physical drop/rattle readiness is earned only by the fixture tests and teardown limits in this pack.

## What commercial PLAUD evidence shows

The public FCC exhibit for the PN0200 NotePin contains four pages of internal photographs. The indexed teardown imagery shows a separate metal casing plate, fitted plastic housing/carrier, lithium pouch, internal assembly and a small mechanical fastener. That supports the same overall architecture: fitted carrier plus fixed components plus cosmetic outer material, not loose development boards inside a hollow shell.

- FCC exhibit index: <https://fccid.io/2A6T3-PN0200/Internal-Photos/Internal-Photos-7518532>
- Mirrored indexed imagery: <https://device.report/manual/13851517>

The photographs do not disclose PLAUD's proprietary tolerances, adhesives or drop-test limits, so Anticipy's values must be qualified independently.
