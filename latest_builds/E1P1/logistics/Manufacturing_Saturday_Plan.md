# Twenty E1P1 units for Boston — manufacturing plan

**No supplier has confirmed a Saturday offer, price, component allocation or reserved slot.** Research refreshed Wednesday, 9 September 2026, around 10:30 Eastern. These five calls are the proposed execution order; none has been made:

1. **AdvancedPCB — 800-979-4722:** request one owner for 22 assembled PCBs, including 20 integrated pendants and two board spares, with all 137 vias filled/capped.
2. **PNC — 973-284-1600; Rush PCB — 408-496-6013:** request parallel alternatives with the same complete scope and arrival deadline.
3. **Micron, Norwood — 781-949-3500 ext. 180:** reserve a local assembly/integration alternative if accepted panels and the complete kit can arrive Thursday.
4. **Upside Parts, Salem — 855-755-2242:** request 20 complete SLA case kits; eligible next-day production requires payment before 3 pm Eastern.
5. **BU mail — 617-353-2307:** clarify receiving before booking delivery; its published processing delay is 24–72 hours after carrier delivery.

Target: **20 complete, tested engineering prototypes, with at least 15 working units in the recipient's hands by Saturday, 12 September**. This is not a promise of 20 qualified customer products. The supplied firmware keeps charging disabled and still lacks integrated, reliable offline NAND recording/backfill. Assembly and a short functional test cannot establish 16-hour operation, 24-hour offline retention, or finished-wearable qualification.

## Recommended route and authoritative files

Start with **AdvancedPCB** because its current capability document explicitly supports nonconductive filled-and-plated-over vias and integrated assembly. It needs to accept a premium exception to its standard assembly schedule. Compare **PNC and Rush PCB in parallel**, with **Micron in Norwood** as a local assembly/integration alternative. Select the supplier that confirms the entire job and arrival plan in writing. Public capability is not a booked production slot.

Use the files in this handoff's **`pcb/`** directory, copied from `Anticipy_E1P1_PCB_Manufacturing_Release_2026-09-09`. Native PCB: `pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb`. Frozen PCB SHA256: `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`. Use the companion CAD, manufacturing process notes, BOM, placements and test instructions from the same handoff.

The job is a **45.75 × 17.88 × 0.80 mm, four-layer FR-4/ENIG board**, with 47 fitted references on two sides, 0201 passives, QFN/WSON packages and a GCT midmount USB connector. Minimum routed trace and clearance are 0.127 mm; smallest bores are 0.200 mm; minimum actual via annulus is 0.125 mm.

**All 137 vias must be nonconductive epoxy-filled, planarized and copper-capped on both sides, IPC-4761 Type VII.** This includes 128 nominal 0.200 mm and nine nominal 0.304 mm pre-fill bores. Keep the four J1 plated mounting slots open. Approve the actual 0.80 mm stackup and 90-ohm differential USB geometry, with 81–99 ohm acceptance and an appropriate coupon. Include panelization, stencil, SPI/AOI/X-ray, programming, first-power/debug support, functional records and enclosure/harness integration. Tenting is not an equivalent substitute for the specified via process.

Quote **22 assembled PCBs: 20 for the pendants and two populated board spares**. At 47 fitted components per board, this is **1,034 fitted SMT placements**. The first two boards are first articles from this same batch; after their test gate, build the remaining 20 PCBs for 18 pendants plus two board spares. Case and battery quantities remain 20 complete sets. Factory feeder attrition and fabrication scrap allowances are additional process quantities, not these two usable spares. Agree which physical functions constitute a pass and how design-related debugging is charged.

## Suppliers checked

| Supplier | Verified public capability and timing | Decision for this job |
|---|---|---|
| **AdvancedPCB — first turnkey decision** | Current facility matrix lists nonconductive-filled and plated-over vias. Detailed assembly page lists 3-, 5- and 10-day turns starting after fabrication and complete parts/data receipt; it supports two-sided SMT, fine pitch, X-ray and functional testing. | Standard timing misses the deadline. Request a named US plant and accepted custom rush schedule covering Type VII, 0.200 mm bores, 90 ohms and all 22 PCB assemblies. [Contact](https://www.advancedpcb.com/en-us/company/contact-us/), [quote portal](https://www.my4pcb.com/), [facility matrix](https://www.advancedpcb.com/getattachment/b691ef44-bc99-4fb4-a208-84d25f49ae30/03-19-2025-APCB-Marketing-Collateral-PDF-for-_Facilities-by-Capabailities_.pdf), [assembly clock](https://www.advancedpcb.com/en-us/solutions/assembly-services/). |
| **PNC — Nutley, NJ** | Same-facility fabrication/assembly; prototypes advertised as short as 24 hours. Supports 0201, two-sided assembly, X-ray, programming and box builds. Lists filled/in-pad vias, 6 mil drills, 20 mil minimum thickness and differential impedance. | Useful parallel option. Its public page does not explicitly confirm copper capping/Type VII or this complete 22-board rush job. Require both. **sales@pnconline.com**; [capabilities](https://www.pnconline.com/capabilities.php), [assembly](https://www.pnconline.com/pcbassembly.php), [RFQ](https://www.pnconline.com/quote_pcb_assembly.php). |
| **Rush PCB — Milpitas, CA** | Explicitly describes via filling, capping and plating. Its detailed turnkey page says fastest 3–4 days, describing 24-hour fabrication plus three days of assembly. | Normal timing is too late for reliable Saturday receipt in Boston. Requires a custom compressed slot and named actual factory. A regional webpage does not prove production takes place there. [Contact](https://rushpcb.com/contact-us/), [portal](https://app.rushpcb.com/), [filled/capped process](https://rushpcb.com/high-density-interconnects/), [turnkey timing](https://rushpcb.com/pcb-manufacturer-florida/). |
| **Micron — Norwood, MA** | Publishes 24–72-hour expedite for small quantities with clean data and ready materials. Supports 01005/QFN/BGA, programming and first-article testing. Timing depends on fabrication/stencil readiness and test needs. | Useful if accepted filled/capped panels and all parts arrive Thursday and a 24-hour assembly/bring-up slot is accepted. One owner must coordinate the upstream fab. **89 Access Road, Norwood**; receiving **781-949-3500 ext. 150**. [NPI timing](https://microncorp.com/prototypes-npi/), [contact/RFQ](https://microncorp.com/contact-us/). |
| **Lightspeed — Haverhill, MA** | Current services include SMT, box builds, X-ray, AOI and functional testing. | Local integration backup; no current numeric turnaround verified. **978-521-7676**; [services](https://www.lightspeedmfg.com/manufacturing), [contact](https://www.lightspeedmfg.com/contact). |
| **Screaming Circuits — Canby, OR** | Offers 24/48-hour prototype assembly and 0201. Complete kit received by noon starts the rolling 24-hour clock. Its 0.75-inch unpanelized minimum exceeds E1's width. | A Thursday-noon complete kit and accepted 24-hour tier could finish Friday. Friday-noon kit receipt is too late for ordinary Saturday Boston arrival. Type VII fabrication is separate. Confirm noon timezone, panel, baking and test time. **866-784-5887**; [FAQ](https://www.screamingcircuits.com/faq), [contact](https://www.screamingcircuits.com/contact-us). |
| **Sierra Circuits** | Turnkey PRO starts at five days generally, but offers **7/10/15-day turns when via-in-pad is present**. Its 24-hour bare fabrication product is different. | Ordinary online timing does not fit Saturday. No custom exception is confirmed. **800-763-7503**; [specific policy and quote entry](https://www.protoexpress.com/products/turnkey-pro/). |
| **PCB Fab Express** | RPS turnkey via-in-pad minimum is seven days, with all vias nonconductive-filled. RPS specifies a 6 mil minimum annulus and no coupon. | E1's 0.125 mm annulus is 4.92 mil, and the required impedance coupon differs from standard RPS. Custom engineering and timing review are required. **408-522-1500**; [specifications/quote](https://ecommerce.pcbfabexpress.com/rpa/?hsLang=en). |
| **Sunstone / American Standard Circuits** | An official indexed capability brochure lists via-in-pad-plated-over. The current complete document and relevant turnkey deadline could not be read; its direct download returned 403. | Reserve only. No Saturday-fit offer verified; inexpensive prototype tiers must not be assumed to include fill/cap and assembly. [Official indexed brochure](https://www.sunstone.com/docs/default-source/capabilities/asc_uhdi_brochure_april_2023.pdf). |
| **JLCPCB / PCBWay** | JLC offers epoxy-filled/capped vias; E1 needs Standard PCBA for 0201/two sides, and its current table lists at least four days. PCBWay's 24-hour assembly clock starts only when boards, parts and all data are ready. | Neither establishes fabrication, procurement, assembly, international shipping and customs to Boston by Saturday. [JLC assembly tiers](https://jlcpcb.com/capabilities/pcb-assembly-capabilities), [JLC fill/cap](https://jlcpcb.com/help/article/pcb-via-covering), [PCBWay start condition](https://www.pcbway.com/assembly-capabilities.html). |

Descriptions of filled, planarized, copper-plated-over vias match the required physical process; the quotation must still explicitly accept **IPC-4761 Type VII**. A statement about filled vias alone is insufficient.

No private design was uploaded and no supplier was contacted. No complete price for 22 PCB assemblies and 20 finished engineering pendants, or delivery commitment has been obtained. Request itemized charges for PCB/fill-cap/impedance, parts, assembly, programming/debug, case/harness integration, expedite and courier. Premium budget remains unquantified until a quote exists.

## Enclosures: the strongest published local option

**Upside Parts, Salem**, offers eligible next-business-day rush FDM/SLA production for paid orders before **3 pm Eastern**. Wednesday acceptance can mean Thursday production completion, followed by courier to the assembly partner or Boston. Production and shipping are separate; quantity, material, finishing and file readiness require acceptance. Request **20 complete case kits** from the final 56 × 35 × 14.8 mm envelope files, including every separate printed item in the mechanical BOM, plus optional spares. [Rush terms](https://www.upsideparts.com/3d-printing/next-day-rush-fdm-sla-nationwide).

Propose fully washed and post-cured tough or ABS-like SLA polymer for the first fit/build. Inspect USB/acoustic openings and internal supports. Retain specified nonmetallic, non-carbon-filled material around the antenna; material substitutions require fit and radio checks. Request a completed fit sample followed by the balance within the reserved run. The case print process is not yet physically qualified.

**855-755-2242**, **sales@upsideparts.com**; 121 Loring Avenue, Salem. Pickup/courier release is Monday–Friday, 7 am–5 pm. [Local production/contact](https://www.upsideparts.com/3d-printing), [quote portal](https://quote.upsideparts.com/). Arrange service-provider courier pickup rather than an offsite trip for the user.

Backup: **Lume 3D**, 9 Knapp Street, Boston; **617-571-9995**, **info@lume3d.co**, Monday–Friday, 9 am–6 pm. It advertises quotes within 24 hours, not guaranteed 24-hour manufacturing. [Official services](https://lume3d.co/). **Empire Group** offers industrial MJF, finishing and assembly, but no Saturday slot was verified. [MJF service](https://www.empiregroupusa.com/3d-printing/multi-jet-fusion).

## Battery transport is a separate deadline

The exact protected pack is **Jauch 246501 / LP561836JU + PCM + two 50 mm wires**. The live procurement audit observed 4,272 units at DigiKey, but that listing explicitly says **“AIR SHIPMENT UNAVAILABLE.”** Stock does not mean overnight delivery is available. [Exact DigiKey listing](https://www.digikey.com/en/products/detail/jauch-quartz/LP561836JU-PCM-2-WIRES-50MM/9560979).

Ask **Jauch US** for the exact protected pack, a confirmed US stock location, and an authorized expedited transport route for 20 units. Jauch publicly describes trained battery-logistics staff and air/road shipping capability, but no exact-pack air allocation or Saturday delivery offer was found. **batterytechnology@jauch.com**; [manufacturer logistics capability](https://www.jauch.com/en-US/products/battery_technology). The alternative is seller-approved expedited or dedicated ground delivery from a confirmed US stock location, only if the seller and carrier accept the arrival deadline. Ordinary ground transit to Boston cannot be assumed to finish by Saturday.

Keep battery transport separate from overnight shipments of bare boards and other electronics. Do not assume installing the cells in equipment makes an unapproved air shipment acceptable. The final shipper must accept the actual pack/equipment configuration. Twenty working battery-powered units also require pack-specific first-power, temperature and harness checks; the supplied firmware still disables charging. A USB-powered board demonstration is not an equivalent delivery of 20 qualified battery-powered wearables.

## Proposed schedule — unbooked

| Time, Eastern | Required result and owner |
|---|---|
| **Wednesday, immediately** | Omar obtains parallel rush decisions from AdvancedPCB, PNC and Rush PCB, and checks Micron's local capacity. The selected factory accepts Type VII, stackup, 22 PCB assemblies for 20 pendants plus two board spares, component allocation, first-article tests and arrival date. |
| **Wednesday before 3 pm** | Accepted SLA rush order for 20 complete case kits at Upside Parts. Factory sources components directly to its receiving dock while fabrication starts; the exact battery pack has a separately accepted transport route. Confirm usable existing inventory and its location before consigning; historical Vancouver delivery is not factory stock. |
| **Thursday** | Filled/capped bare panels, electrical-test/coupon results, stencil and complete component kit reach the reserved line. The first two assemblies are programmed and tested immediately. Cases reach the integration point. |
| **Friday before agreed dispatch cutoff** | The remaining 20 PCBs are assembled, inspected, programmed and tested: 18 join the first two as pendants, and two remain populated board spares. Install approved battery/motor harnesses, case and acoustic/LED parts on the 20 pendants; record each unit's serial number and results. Prefer same-day local courier if the integration partner is near Boston. |
| **Friday preferred; Saturday only with explicit handoff** | Deliver all 20, with at least 15 passing units as the minimum target, to 33 Harry Agganis Way. Book the required expedited or Saturday service. A factory ship date or carrier scan is not recipient access. |

A 24-hour assembly slot starting Thursday noon ends Friday noon, leaving limited time for debugging, integration and shipment. Missing parts or a failed first article can break the schedule. Do not release the balance as working if the first article fails. The supplied charging-disabled firmware and incomplete offline path remain engineering limitations; do not advertise runtime, retention or finished-product qualification based on workmanship tests.

## Boston receiving: account for processing time

User-supplied destination:

**[Recipient name exactly as registered with BU]**  
**Box 8577**  
**33 Harry Agganis Way**  
**Boston, MA 02215, USA**

Use “Box”, not “P.O. Box”. BU identifies 33 Harry Agganis Way as its own mailroom. Academic-year hours beginning September 8 are Friday 9 am–6 pm and Saturday/Sunday noon–5 pm. Standard collection requires the DormMail notification and Terrier Card. [BU mail/address policy](https://www.bu.edu/housing/services/mail/).

**BU says processing can take 24–72 hours after the carrier marks a parcel delivered.** Saturday mailroom delivery therefore cannot by itself meet a Saturday-in-hand deadline. [Current BU FAQ](https://www.bu.edu/housing/services/mail/mailroom-faqs/). Prefer Friday arrival with agreed handling, or a permitted direct courier-to-recipient handoff at the same building. This requires no offsite pickup and does not presume room-door access. Confirm recipient name, phone, building access and handoff point. No arrangement has been made. **617-353-2307**, **dormmail@bu.edu**.

## Existing orders are different builds

The parent email audit found no current manufacturer promise for Saturday. JLC order **SMT026083160845** (5 September) authorized an older NOR-flash substitute, C190799 / MX25L25645GM2I-08G; it is not the new NAND-based E1P1 release. SAPA / Carina discussed an older ten-unit XIAO trial and drop-off on 4 September, not a booked E1 custom PCBA run. That existing contact may help with a separately agreed fallback: **604-520-5611 ext. 1**, **orders@sapatechs.com**, 3202 Beta Avenue, Burnaby. Neither historical conversation establishes current capacity, component allocation or Boston delivery.

This plan is ready for Omar to execute. It is a public-source manufacturing plan for engineering prototypes, not a placed order, reserved slot, shipping guarantee or customer-product qualification.
