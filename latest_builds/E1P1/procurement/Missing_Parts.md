# E1P1 parts to complete 20 prototypes

This list matches the corrected PCB release ending **78fe…bec36**: **22 PCB assemblies for 20 engineering prototypes plus 2 spare PCBAs**. The 27 SMT groups and 47 placements per board were reconciled against the released BOM. Supplier stock is unreserved.

## Locate these before buying replacements

| Exact item | Recorded purchase | Delivery evidence | Apply if counted and accepted by assembler | New purchase after acceptance |
|---|---:|---|---:|---:|
| Raytac MDBT50Q-1MV2 | 25 | Package delivered in BC, Sep 3 | 22 | 0 |
| Alpha & Omega AO3400A | 25 | Package delivered West Vancouver, Sep 1 | 22 | 0 |
| Omron B3U-1000P | 20 | Same delivered DigiKey package | 20 | 2 for spare PCBAs |
| Vybronics VCLP1020B002L motor | 20 | Same delivered DigiKey package | 20 | 0 |

These are invoice quantities in delivered packages. **Usable counts and arrival at the assembler/Boston are unverified.** Fresh Gmail checks on September 9 found no later relevant purchase receipt. Count, label and consign these exact parts; do not automatically reorder them.

## Buy or have the assembler source

- **20 protected Jauch batteries**, exact **LP561836JU+PCM+2 WIRES 50MM / 246501**. Live stock 4,272 at 14:31 UTC; $179.20 for 20 before charges. **Air shipment unavailable through this listing.** Obtain an accepted ground/dangerous-goods delivery lane before relying on Saturday. [DigiKey](https://www.digikey.com/en/products/detail/jauch-quartz/LP561836JU-PCM-2-WIRES-50MM/9560979)
- **20 TDK B57540G1103F000 thermistors**. Live stock 6,219 at 14:31 UTC; $58.36 for 20 before charges. Battery has no built-in NTC. [DigiKey](https://www.digikey.com/en/products/detail/epcos-tdk-electronics/B57540G1103F000/3500367)
- **The SMT quantities below**, including the two spare PCBAs. These total **970 new SMT pieces if the recorded stock above is usable and accepted**. Without that stock, the maximum SMT requirement is 1,034 pieces. The CSV keeps both quantities. Additional assembler feeder/leader/attrition allowance is separate.

| Exact released MPN | References | Buy after stock acceptance |
|---|---|---:|
| RC0402FR-0710KL | R13 R7 R12 | 66 |
| RC0402FR-07100KL | R6 | 22 |
| GRM188R61E106MA73D | C7 C8 C2 C4 C3 C10 C9 | 154 |
| EMK107BB7225KA-T | C6 | 22 |
| TPD2EUSB30ADRTR | U4 | 22 |
| CIGT201610EH2R2MNE | L1 L2 | 44 |
| RC0201FR-0710KL | R2 R1 | 44 |
| APHB1608LVBDSEKJ3C | LED1 | 22 |
| B3U-1000P | SW1 | 2 |
| NPM1300-QEAA-R | U2 | 22 |
| RC0402FR-07100RL | R5 R8 | 44 |
| USB4500-03-1-A | J1 | 22 |
| C0402C104M4RACTU | C14 C15 C16 | 66 |
| C1005X7R1C104K050BC | C17 C19 C22 | 66 |
| 1N4148WS-13-F | D1 | 22 |
| C0603X5R1E104K030BB | C13 | 22 |
| TPD2E2U06DCKR | U6 | 22 |
| CRCW02010000Z0ED | R11 R10 | 44 |
| GRM155R60J106ME15D | C26 C25 | 44 |
| CMM-3424DT-26165-TR | MIC1 | 22 |
| GRM21BR60J476ME01L | C23 | 22 |
| RC0201FR-07150KL | R3 R4 | 44 |
| ESD441DPYR | D2 | 22 |
| C1608X7R1C105K080AC | C1 C18 C5 | 66 |
| MX35LF4GE4AD-Z4I | U5 | 22 |

Every SMT source URL and observation time is in the CSV. 26 groups have sufficient observed stock. **U1 is the exception:** 14 marketplace modules with about 14-day dispatch cannot meet this batch; the previously delivered modules are the practical first route.

## Small parts the electronics BOM does not include

Ask the assembly shop to supply these to the CAD dimensions; exact material SKUs and stock are not confirmed:

- 20 current case sets, including lid, base and button; 20 separate clear lightpipes and optical adhesive.
- **40 M2 ×4 mm screws**, head no larger than 4.0 mm diameter ×1.3 mm high. Optional four extra screws. Old M2 ×8/10/12 screws and nuts do not match.
- **20 microphone gasket rings**, OD2.7 / ID1.2 / free height 0.4 mm. No additional dust mesh is released.
- **80 PCB capture pads**, four per case, 0.8 ×0.6 ×0.3 mm.
- 20 battery retention pieces: removable electrically insulating adhesive, **≤0.20 mm compressed**, preserving 0.05 mm installation reserve.
- 20 motor retention arrangements; 20 insulated NTC attachment/lead sets; 20 fine textile cord sets.

Battery and motor leads are supplied with those parts. NTC leads are supplied too. Use the dimensional harness contract rather than buying unnecessary connector sets. Generic tape, heat-shrink and wire already ordered cannot be credited until their installed size and material suitability are checked.

## Tools and items to avoid buying twice

Locate the already ordered soldering tools, DMM, microscope, 28 AWG wire, polyimide tape, heat-shrink, flux and IPA. Confirm delivery and usable condition. The generic DAPLink programmer needs an actual compatibility test; otherwise use the assembler's commercial SWD programmer and a custom fixture. Require two known-good USB-C data cables and suitable bench power/current measurement. Ten cables were previously **held** at Memory Express; collection and payment remain unconfirmed. A 20-cable customer bundle is not included in the base plan.

Do not buy the old XIAO/microSD basket for E1P1. Purchased PN2222ATF, 1N4148/1N4148W-HF, 0805 resistors/capacitors and Lee's P-channel MOSFET do not match the current footprints/parts. Adafruit3814 JST sets are evaluation stock, not an approved battery harness. The older JLC NOR-flash order is a different board and does not fulfill this NAND release.

The files support prototype manufacture. Physical first-article tests, battery charging qualification and complete offline NAND recording/recovery remain unfinished. Charging is disabled in bench firmware; 16-hour runtime is not demonstrated. No order, supplier message or email was sent in this audit.
