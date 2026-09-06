# JLCPCB order status

Checked against the latest saved email as of 2026-09-04 18:03 PDT.

## Identifiers

- Web order: `W2026083114248171`
- PCBA order: `SMT026083160845`
- Project/order reference in subject: `13417400A`
- Original mismatched JLC part: `C526821`
- Requested replacement: `C190799 / MX25L25645GM2I-08G`

## What happened

JLCPCB reported that C526821 did not match the PCB pads and could not be assembled. Omar chose the replacement-parts route and requested C190799, subject to an engineering check of the SOP-8 208/209 mil footprint, pin-1 orientation and net mapping.

## Latest JLCPCB response

Grace said JLCPCB will proceed with the order and asked the customer to wait. She specifically said the orientation must be checked in the final DFM when it becomes available.

## Current gate

- No final DFM was attached to the latest email.
- The email does not confirm that the footprint/pin/net check has passed.
- The order should not be treated as electrically cleared until the final DFM is reviewed and the C190799 orientation/net mapping is confirmed.
- The email record does not prove which local KiCad revision was uploaded to JLCPCB.

## Exact next action

Open the existing JLCPCB order account used for `SMT026083160845`, wait for the final DFM/replace-parts action, select C190799 if still required, and have the hardware engineer verify the footprint, pin 1 and nets before approving assembly. Do not approve C526821 or an unpopulated memory position.
