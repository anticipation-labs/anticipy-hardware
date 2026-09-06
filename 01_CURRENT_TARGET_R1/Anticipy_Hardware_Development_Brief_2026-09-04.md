**PRODUCT + ENGINEERING HANDOFF**

**Anticipy Hardware Development Brief**

Custom PCB and investor-ready metal wearable \| Rev 1 \| September 4,
2026

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>The job in one sentence</strong></p>
<p>Build a small, polished pendant that continuously captures useful
speech, sends it to the Anticipy iPhone app, safely stores audio while
the phone is unavailable, and gives discreet haptic feedback.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

# Start here: what each person owns

## Omar / Anticipy provides

- The existing XIAO nRF52840 Sense boards used as the known working
  reference.

- Access to the current Anticipy iPhone test build and the current
  firmware/source or binary.

- A contact who can confirm the BLE UUIDs, packet format, codec,
  commands, and backfill behavior.

- The Anticipy logo, color direction, and a few exterior reference
  images.

## The hardware engineer owns

- System architecture, component selection, schematic, PCB layout,
  antenna/RF plan, power budget, and battery selection.

- Industrial/mechanical CAD, internal carrier, metal covers, acoustic
  openings, charging approach, tolerances, and assembly method.

- Prototype procurement, assembly, bring-up, firmware porting support,
  testing, design corrections, and production files.

- A clear written record of decisions, risks, costs, lead times, and
  what still needs approval.

## What success looks like

**First success:** one closed, pocketable, body-worn unit that works
reliably with the real iPhone app and looks intentional from every
angle.

**Next success:** three matching CNC-aluminum EVT units, each with a
serial number and passed test record.

**Then:** a corrected Rev B design suitable for a ten-unit
founder/investor batch.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Do not build these</strong></p>
<p>No camera, display, speaker, external daughterboards, loose stacked
dev boards, taped-on parts, or a copied Plaud enclosure. The product
must be recognizably Anticipy.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

# 1. Product requirements

## The user experience

- The user wears Anticipy on a necklace or clip. It works ambiently;
  normal use should not require deliberate gestures.

- The microphones capture speech and firmware sends a mono audio stream
  to the Anticipy iPhone app over Bluetooth Low Energy.

- If the phone is temporarily unavailable, the pendant timestamps and
  stores compressed audio locally, then backfills in order when the
  phone returns.

- The app can command a short, discreet vibration. The device also
  reports battery, connection, storage, firmware, and health status.

- One subtle physical control is allowed for power, privacy/mute,
  pairing, or factory reset. Status light must be discreet, not visually
  dominant.

## Requirements matrix

| **Area**                   | **Status** | **Requirement**                                                                               |
|----------------------------|------------|-----------------------------------------------------------------------------------------------|
| **Camera/display/speaker** | **Fixed**  | None.                                                                                         |
| **Phone**                  | **Fixed**  | iPhone is the primary companion and cloud gateway.                                            |
| **Connectivity**           | **Fixed**  | Reliable BLE live audio, commands, status, reconnect, and ordered backfill.                   |
| **Offline storage**        | **Target** | At least 16 hours of compressed audio; design for 20 hours with margin.                       |
| **Battery life**           | **Target** | At least 16 hours in the real Anticipy use case, measured on a closed unit.                   |
| **Size**                   | **Target** | Aim for 51 x 21 x 11 mm. Do not exceed +10% per axis without written approval.                |
| **Weight**                 | **Target** | Aim for 20 g or less. Flag any design above 25 g before fabrication.                          |
| **Audio**                  | **Fixed**  | Clear body-worn conversational speech; no severe clothing-rub or haptic contamination.        |
| **Exterior**               | **Fixed**  | Premium rounded pill, Anticipy branding, clean seams, no rattle, no exposed prototype wiring. |
| **Durability**             | **Target** | Everyday sweat/splash resistance and 1 m drops; do not claim an IP rating before testing.     |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Reference, not a copy</strong></p>
<p>Plaud NotePin/NotePin S is only the size-and-finish benchmark.
Official specifications list 51 x 21 x 11 mm, about 17 g, two MEMS
microphones, and an aluminum-alloy plus polycarbonate construction.
Anticipy needs original geometry, branding, fastening, acoustic design,
and internal architecture.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

# 2. Electrical architecture and custom PCB

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Recommended Rev A direction</strong></p>
<p>Keep the nRF52840 software family for the first custom board so the
current XIAO firmware and iPhone integration are portable. Prefer a
compact certified module if it materially lowers RF risk; use a bare SoC
only if the engineer can own antenna tuning, certification risk, and
schedule.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## Required functional blocks

**MCU + BLE:** nRF52840-compatible starting point; enough RAM/flash for
codec, buffering, encrypted transport, DFU, and diagnostics.

**Microphones:** One or two low-power digital MEMS microphones. Prefer
two footprints and populate based on measured benefit. Process to one
outgoing mono stream.

**Local storage:** QSPI NOR flash sized from the actual codec. Plan 512
MB unless the calculation and wear model justify less.

**Power:** Protected Li-ion/LiPo, charger, power-path behavior, battery
gauging, undervoltage protection, ESD, and measured current rails.

**Haptics:** Thin ERM or LRA plus a proper driver. It must be felt
through clothing without resetting the radio or overwhelming the
microphones.

**Controls/status:** One button or switch, discreet LED/light pipe if
needed, and a reliable factory-reset path.

**Charging/data:** Preferred: sealed rear contacts and a small USB-C
puck. Schedule fallback: a clean recessed USB-C port on Rev A.

**Programming/test:** SWD access, serial identity, test pads for
rails/signals, current measurement, and a pogo fixture plan.

## Non-negotiable design work

- Capture the current BLE/app protocol before freezing the schematic:
  UUIDs, packet framing, timing, codec, commands, authentication,
  reconnect, backfill, and errors.

- Provide a measured power budget for live streaming, disconnected
  recording, idle, haptic, charging, and firmware update. Battery life
  is accepted only after a closed-unit test.

- Size storage using: bitrate x seconds / 8, then add at least 25% for
  metadata, filesystem overhead, bad sectors, logs, and wear. Example:
  20 hours at 16 kbps needs about 180 MB with that margin.

- Keep the RF antenna and matching network away from battery, metal,
  ground pours, fast clocks, and the user-facing metal cover; include an
  RF test point or connector where practical.

- Add ESD protection, reverse-polarity/short protection, safe charge
  limits, and clear battery isolation. Never compress, bend, or trap a
  pouch cell.

- Store local audio encrypted, bind the pendant to its owner, support
  signed/validated firmware updates, and erase buffered audio only after
  confirmed transfer.

## Rev A PCB guidance

**Board:** 4-layer rigid PCB is the default. Use rigid-flex only if a
real space or assembly benefit offsets cost and schedule.

**Assembly:** Prefer SMT parts on one side where possible, no hand-wired
production connections, and explicit keep-outs for microphones, antenna,
fasteners, battery, and charging contacts.

**Firmware continuity:** The custom board should preserve the existing
app behavior. Any protocol change must be documented and agreed with the
iOS developer before layout release.

# 3. Mechanical and industrial design

## Recommended construction

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Fastest credible premium build</strong></p>
<p>Use a PC+ABS, MJF nylon, or SLA internal carrier that locates the
PCB, battery, microphones, motor, contacts, and seals. Add CNC-machined
6061 aluminum front and back cosmetic covers. This gives a premium metal
feel while protecting RF, acoustics, and assembly tolerances.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

- Prototype the full internal stack and cover geometry in SLA before
  CNC. The printed assembly must close without pressure and pass audio,
  antenna, charging, haptic, and drop pre-tests.

- Keep a deliberate non-metal RF window adjacent to the antenna. Do not
  enclose the antenna inside a continuous metal box.

- Give each microphone a short, sealed acoustic path with mesh and
  gasket. Keep adhesive out of the port and isolate the mic from the
  motor and hard contact with the shell.

- Use hidden screws, snaps, or controlled adhesive joints. The enclosure
  must be openable during EVT without damaging the battery; no loose
  foam, rattling parts, or tape visible from outside.

- Provide compliant battery clearance, a rigid protective bridge if
  parts stack above it, strain relief for leads, and no sharp edges or
  point loads near the pouch.

- Include an intentional chain passage or clip interface. It must not
  weaken the shell, block microphones, or sit inside the antenna
  keep-out.

- Model assembly order, tool access, tolerance stack, adhesive
  thickness, gasket compression, and cable bend radii. Nominal fit alone
  is not enough.

## Material and finish decision

| **Part**             | **Rev A recommendation**                                  | **Reason**                                                                           |
|----------------------|-----------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Outer covers**     | CNC 6061-T6 aluminum, bead-blasted + anodized             | Fast, repeatable, premium, lighter and easier to machine than titanium.              |
| **Internal carrier** | Black or natural PC+ABS / MJF PA12 / engineering SLA      | Controls fit, creates RF window, locates components, and isolates the battery.       |
| **Acoustic seal**    | Purpose-made mesh + thin silicone gasket                  | Protects the port while maintaining a repeatable sound path.                         |
| **Battery pad**      | Thin flame-rated or specified pressure-sensitive material | Prevents movement without squeezing the pouch.                                       |
| **Titanium**         | Evaluate after Rev A passes                               | Use only if weight, RF, machining cost, finish, and lead time are proven acceptable. |

## Exterior quality bar

- Original Anticipy silhouette; compact rounded pill, not a clone of
  another product.

- Even seam and finish, clean logo, no sharp edges, no visible glue
  squeeze-out, no exposed layer lines, and no audible rattle.

- Charging, microphone, button, LED, and chain features must look
  intentional and be located from the complete internal stack, not added
  afterward.

# 4. How we will build it

## Checkpoint A: 24-48 hour engineering audition

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Purpose</strong></p>
<p>Before expensive fabrication, show how you think. Do not merely
redraw the old prototype. Identify contradictions, make recommendations,
and quantify the risks.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

- One system block diagram and a written architecture recommendation.

- Current XIAO/app compatibility plan, including what must be measured
  or captured from the existing firmware.

- Preliminary BOM with manufacturer part numbers, size, cost,
  availability, lifecycle status, and at least one substitute for
  critical parts.

- Power and storage calculations with best/expected/worst cases.

- Preliminary PCB outline/stack and a mechanical cross-section showing
  the complete component stack.

- Recommended material/finish, charging method, prototype quantities,
  schedule, estimated cost, and top ten risks.

- A short list of requirement exceptions. Every exception must explain
  why and propose a specific alternative.

## Checkpoint B: prove the electronics

1.  Reproduce the current XIAO-to-iPhone audio flow and record the
    protocol as the baseline.

2.  Bring up the Rev A custom PCB on the bench: power, charging,
    microphones, BLE, storage, haptics, button, LED, DFU, and diagnostic
    logging.

3.  Run power, RF, audio, haptic-noise, storage/backfill, charging, and
    thermal tests before enclosing it.

## Checkpoint C: prove the enclosure

1.  Print one complete SLA/MJF fit unit using the real PCB, real
    battery, real motor, real fasteners, real gaskets, and real adhesive
    thickness.

2.  Fix fit, acoustic, antenna, haptic, charging, and assembly issues in
    the printed unit.

3.  Only then release CNC drawings for three 6061-aluminum EVT units.

## Checkpoint D: close the unit and test it

1.  Assemble three serialized EVT units using the documented process.

2.  Test each unit closed, body-worn, with the real iPhone app. Record
    every result and failure.

3.  Correct the design into Rev B. Freeze files only after all release
    gates pass.

## Checkpoint E: ten-unit founder/investor batch

**Build only after approval:** ten matching Rev B units plus spares
using the same BOM revisions, material/finish specifications, firmware
version, assembly process, and test record.

# 5. What the engineer must hand back

## Electrical design package

- Native schematic and PCB source files, schematic PDF, board STEP
  model, fabrication drawings, stack-up, controlled-impedance notes,
  Gerbers or ODB++, drill files, IPC netlist, pick-and-place, and
  assembly drawings.

- BOM with exact manufacturer part numbers, approved substitutes,
  distributor links, pricing at 1/10/100/1,000 units, lifecycle and
  availability notes.

- Antenna layout/keep-out and RF test plan; power-tree diagram;
  charger/protection details; test-point map; programming and
  production-test fixture design.

- Board bring-up checklist, measured current table, known issues,
  engineering changes, and revision history.

## Mechanical design package

- Native CAD plus STEP for the full assembly and every manufactured
  part.

- Dimensioned 2D drawings with tolerances/GD&T, material, finish, color,
  surface texture, thread/fastener notes, gasket/adhesive specification,
  and critical-to-quality dimensions.

- Exploded view, assembly order, cross-sections, tolerance-stack report,
  mass properties, antenna/acoustic keep-outs, and battery no-pressure
  clearance proof.

- Print-ready fit-check files, CNC RFQ pack, and a vendor-ready
  inspection checklist.

## Firmware and interface package

- Source repository, build instructions, pin map, release binary,
  version/hash, bootloader/DFU procedure, factory-reset path, and
  recovery steps.

- BLE protocol document: services/characteristics, codec, packet format,
  timestamping, acknowledgements, encryption/owner binding, commands,
  backfill, error codes, and version compatibility.

- Manufacturing test firmware plus a normal diagnostic mode that reports
  mic, flash, battery, charging, haptic, button, radio, reset cause, and
  firmware version.

## Manufacturing and QA package

- Supplier list, quotes, lead times, minimum order quantities, approved
  materials, incoming inspection, assembly SOP, rework limits, and
  shipping/battery paperwork.

- One serial-numbered test record per unit, photographs of the closed
  unit, measured dimensions/weight, and a signed release checklist.

- Everything must be editable source, not screenshots or flattened
  exports only. Anticipy receives all project files and credentials
  needed to reproduce the build.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Important release rule</strong></p>
<p>A beautiful enclosure is not a working unit. A working board in a
rough shell is not an investor unit. Both the closed hardware and the
real Anticipy app flow must pass together.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

# 6. Acceptance tests for each EVT unit

| **Gate**             | **Pass condition**                                                                                                                                                                 |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **App + BLE**        | Owner pairing succeeds; reconnect is automatic; control cannot silently transfer to a second phone; live audio, status, commands, and backfill work with the current app.          |
| **Audio**            | Body-worn quiet-room and normal-conversation recordings are intelligible; no severe RF ticks, charging noise, clothing rub, occlusion, or haptic contamination.                    |
| **Storage**          | A forced disconnection fills and backfills the intended buffer in correct time order with no duplicate, missing, or corrupt segments. Capacity meets the agreed 16-20 hour target. |
| **Battery**          | Measured closed-unit run time meets the agreed 16-hour use-case target; gauge and low-battery behavior are predictable; no unexpected reset or deep discharge.                     |
| **Charging/thermal** | Safe charge current and termination are verified. Cell and surface temperatures remain within the battery vendor limits and the agreed skin-contact limit during charge and use.   |
| **Haptics**          | 100 commanded pulses work without brownout, disconnect, loose parts, or unacceptable microphone contamination.                                                                     |
| **RF**               | Stable body-worn operation at 5 m and room-scale operation at 10 m in the agreed test environment; antenna performance is checked with metal covers installed.                     |
| **Mechanical**       | Meets approved size/weight; no pressure on the battery; even seams; no rattle; charging/controls/attachment work after drop and handling tests.                                    |
| **Drop/handling**    | Passes the agreed 1 m multi-face drop sequence, charging-contact cycles, chain/clip pull, shake, and light torsion tests without opening or losing function.                       |
| **Security/update**  | Local audio is encrypted; owner binding works; firmware update and recovery work; reset procedure is intentional and documented.                                                   |

## Stop conditions

- Do not close or ship a unit if the battery is squeezed, punctured,
  hot, unprotected, undocumented for transport, or able to move inside
  the enclosure.

- Do not release CNC if the complete SLA fit unit has not passed
  closure, audio, RF, charge, haptic, and battery-clearance checks.

- Do not build ten if any of the three EVT units needs a different
  hand-fitted fix. Correct the CAD/PCB/process first.

- Do not claim waterproofing, battery life, range, or certification from
  calculations alone. Test and record it.

# 7. Decisions the engineer should recommend

**These are not homework for Omar before kickoff.** The engineer should
present a recommendation, evidence, cost, and schedule impact for each
item at Checkpoint A.

**MCU implementation:** nRF52840 module vs. bare SoC vs. another
compatible low-power BLE platform.

**Microphone count:** One vs. two digital MEMS microphones based on
actual transcription and noise tests.

**Audio transport:** Codec, frame size, BLE throughput, retransmission,
buffering, clock/timestamp strategy, and iOS background behavior.

**Storage:** Flash type/capacity and wear strategy that meet 16-20 hours
with the selected codec.

**Battery:** Capacity, dimensions, protected cell/pack, supplier,
certification, run time, charging current, and enclosure clearance.

**Charging:** Sealed contact puck vs. clean recessed USB-C for Rev A,
including ESD and mechanical life.

**Haptics:** ERM vs. LRA, driver, mounting, feel, current, and acoustic
contamination.

**Materials:** 6061 aluminum Rev A; whether titanium adds enough value
to justify its weight, RF, machining, cost, and schedule effects.

**Attachment:** Chain passage, clip, magnetic accessory, and how it
affects acoustics, RF, strength, and size.

**Environmental target:** Realistic splash/sweat sealing and the
validation path before making any IP claim.

## What is out of scope for this first hardware engagement

- Cloud AI behavior, app redesign, BCI/EMG add-ons, cameras, displays,
  speakers, and gesture-driven interaction.

- Injection-mold tooling or large production orders before the Rev B
  design and test process are frozen.

- Titanium mass production before the aluminum EVT design passes and a
  specific titanium RF/mechanical plan is approved.

# Omar: your only four actions

1.  Send this brief to the hardware engineer.

2.  Hand him two XIAO nRF52840 Sense boards and give him access to the
    Anticipy iPhone test build/current firmware.

3.  Send the Anticipy logo plus the preferred color/finish images.

4.  Ask him to return Checkpoint A within 24-48 hours. Approve
    fabrication only after that review.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>The exact kickoff message</strong></p>
<p>“Please read the attached Anticipy hardware brief. Start with
Checkpoint A and tell me where the requirements conflict or create risk.
I want your recommended architecture, preliminary BOM, power/storage
math, PCB outline, enclosure cross-section, schedule, cost, and top
risks before we release any PCB or CNC order.”</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>
