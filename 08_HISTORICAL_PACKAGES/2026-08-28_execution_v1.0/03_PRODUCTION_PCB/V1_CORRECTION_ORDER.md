# v1.0 PCB correction order

## Tiny answer

This green board is **not ready to order**. Keep the useful nPM1300, microphone,
test-point and board-outline work, then make these corrections in this order.

## Must-fix before routing

1. Replace U1 with the official Raytac **AN54LV-15** symbol and land pattern.
   It has its own chip antenna, so remove the old external antenna and matching
   network. Preserve the no-copper/no-metal region from Raytac's controlled
   design guide.
2. Replace U4 raw W25N04KV NAND with **MK Founder MKDV4GCL-ABF** managed
   SD-NAND. Its LGA-8 pinout is: 2 CS, 3 CLK, 4 GND, 5 MOSI, 6 MISO, 8 VDD;
   pins 1 and 7 are DAT2/DAT1. Do not reuse the W25N footprint or pad map.
3. Replace SW1 with **PTS841GMSMTRLFS**, using the Littelfuse/C&K controlled
   drawing and side-actuator orientation.
4. Replace the motor FPC landing zone with two wire solder pads for
   **Vybronics VC0720B015F**, plus holes/adhesive features providing strain
   relief. Motor retention belongs in the chassis, not in its wires.
5. Fix U6 DRV2605L: ball A2/REG is the driver's 1.8 V regulator output. It is
   **not 3V0**. Connect A2 only to the required 1 uF bypass capacitor to ground
   and label the net `HAPTIC_REG`.
6. Resolve every `*_TO_U1_PAD_TBD` net against the official Raytac pin map.
7. Freeze every passive MPN and verify voltage bias, tolerance, temperature,
   footprint and approved alternates.

## Then

1. Route power first, then RF keepout, PDM microphones, storage and signals.
2. Run unfiltered KiCad ERC and DRC.
3. Export the populated PCB STEP and put it into the exact production shell.
4. Obtain assembler DFM approval.
5. Order **three EVT boards only**.

The 481 MB managed storage covers the controlled 414,000,000-byte backlog with
about 16.2% raw capacity headroom. Filesystem, encryption, journal and recovery
overhead must stay inside that same headroom; if firmware requires 20% free
space in addition, choose a larger managed device.
