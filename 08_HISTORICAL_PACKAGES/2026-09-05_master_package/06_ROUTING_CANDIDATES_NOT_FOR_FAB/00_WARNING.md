# Routing evidence only - not a fabrication release

These boards are independent, DRC-clean subsystem experiments. They start from
the same clean master and are not cumulative. Do not blindly merge their copper
and do not export Gerbers from any of them.

- The power candidate proves 134 remaining connections from the 176-connection
  base, but still has exposed-pad and protected-VBUS decisions open.
- The USB candidate proves the fanout and matched pair, but requires the actual
  fabricator stack-up, impedance geometry, and CAM approval.
- The audio/storage candidate proves selected PDM and NAND signal paths, but
  storage firmware and clock-margin testing remain open.
- The miscellaneous candidate covers selected low-speed routes only.

A senior KiCad engineer may use these as routing evidence. The final board must
be rebuilt/consolidated under full-board DRC, connectivity, ERC, DFM, RF, power,
mechanical, and peer-review gates. Release still requires zero unconnected
items.

