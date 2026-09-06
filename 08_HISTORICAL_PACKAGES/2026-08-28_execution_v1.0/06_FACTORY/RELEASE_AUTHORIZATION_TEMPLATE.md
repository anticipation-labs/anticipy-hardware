# Factory release authorization

This form is intentionally blank. A quote, email acknowledgement or uploaded file is not manufacturing authority.

## Work order

| Field | Released value |
|---|---|
| Release ID |  |
| Phase | EVT / DVT / PVT |
| Supplier/legal site |  |
| Purchase order |  |
| Required accepted quantity |  |
| PCB revision and Gerber SHA-256 |  |
| BOM revision and SHA-256 |  |
| CPL revision and SHA-256 |  |
| Panel drawing revision and SHA-256 |  |
| Mechanical revision and drawing SHA-256 |  |
| Battery pack revision and drawing SHA-256 |  |
| Firmware version and SHA-256 |  |
| Factory-test version and SHA-256 |  |
| Assembly traveler revision |  |
| EOL specification revision |  |
| Approved deviations | None / listed IDs |
| Earliest permitted production start |  |
| Required hold points |  |
| Authorized by / UTC timestamp |  |

## Required declarations

- [ ] Every manifest item required for this phase is present, independently viewed and hash-verified.
- [ ] All unexplained ERC, DRC and supplier DFM findings are closed.
- [ ] PCB stack-up, panel and assembly capability are accepted in writing.
- [ ] Complete orderable BOM and availability are accepted; substitutions are disabled except approved alternates.
- [ ] Approved battery drawing, polarity, NTC/charge limits and transport/safety evidence are recorded.
- [ ] Populated PCB STEP and released enclosure close without collision or battery pressure under the signed tolerance stack.
- [ ] Programming/test files reproduce their recorded hashes and fixture calibration is current.
- [ ] Prior phase gates pass and all ECOs affecting this build are incorporated.
- [ ] Compliance status permits the planned build/use; customer shipment remains separately gated.

## Authorization statement

> Fabricate and assemble only the phase, revision and quantity listed above. Stop at every named hold point. Do not substitute, repair, reprogram, overbuild, ship or continue after a lot-stop condition without written disposition tied to this release ID.

Signature/authorization: ____________________  UTC: ____________________

