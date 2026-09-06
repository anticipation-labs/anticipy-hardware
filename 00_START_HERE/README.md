# 00 — Start here

Read in this order.

| # | File | Why |
|---|---|---|
| 1 | [`HARDWARE_STATE.md`](HARDWARE_STATE.md) | One page: what is actually true today. Where the project really stands, and the one deadline that is live. |
| 2 | [`CONTRADICTIONS.md`](CONTRADICTIONS.md) | **The most important file here.** Seventeen places where two documents in this repository disagree — on the processor, the enclosure size, the battery, which board file is real, and whether the firmware can drive the haptics. Read it before acting on any single document. |
| 3 | [`GLOSSARY.md`](GLOSSARY.md) | Decodes R0 / R0B / EVT-A / R1 / XIAO / P2S / EOL / DFM and the part numbers, none of which are defined anywhere else. |
| 4 | [`PROVENANCE.md`](PROVENANCE.md) | Where every file came from, how the audit was done, and what was deliberately excluded. |

## If you are the incoming hardware engineer

Your assignment is in [`../01_CURRENT_TARGET_R1/`](../01_CURRENT_TARGET_R1/). Before you start,
know these four things:

1. **Nothing here is fabrication-ready.** No Gerber, ODB++, drill, pick-and-place or assembly
   drawing exists anywhere. That is deliberate, not an oversight.
2. **There is a live JLCPCB order** sitting on an unverified part substitution. It is the only
   clock running. See [`../07_PROCUREMENT/`](../07_PROCUREMENT/).
3. **Three custom boards were started and none finished**, and the one named "older" (R0) is
   further along than the one presented as current (R0B).
4. **The briefs disagree with each other.** The newest brief specifies a different processor and a
   different enclosure size than the most complete package on disk. Nobody wrote down why.

## If you are looking for one specific thing

| Looking for | Go to |
|---|---|
| What to build | `../01_CURRENT_TARGET_R1/` |
| The BLE wire protocol | `../05_FIRMWARE/DOCS/PROTOCOL.md` |
| Security and privacy analysis | `../05_FIRMWARE/DOCS/THREAT-MODEL.md` |
| How to reproduce a firmware build | `../05_FIRMWARE/DOCS/BUILD.md` |
| What actually ran on a device | `../05_FIRMWARE/DEVICE_RECOVERY/` |
| Parametric enclosure source | `../04_MECHANICAL/OPENSCAD_SHELL_PROGRAM_v5.1/` |
| The only machinist drawing | `../04_MECHANICAL/MACHINIST_DRAWINGS/` |
| Factory acceptance and EOL tests | `../06_FACTORY_AND_QA/FACTORY_RELEASE_PROCESS/` |
| The PCB routing history | `../03_PCB/R0_ROUTING_HISTORY_NOT_FOR_FAB/` (a git repo) |
| An original untouched deliverable | `../08_HISTORICAL_PACKAGES/` |
