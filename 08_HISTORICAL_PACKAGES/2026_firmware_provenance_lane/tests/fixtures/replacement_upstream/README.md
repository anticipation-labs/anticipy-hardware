# Replacement patch fixture

These four text files are exact copies from BasedHardware/Omi commit
`ee9892562648f074e3c6b59d508127d81fa21010`, source tree
`Friend/firmware/firmware_v1.0`. Their Git blob IDs are asserted against
`firmware/upstream.lock.json` before the replacement patch test runs.

The fixture makes patch application, protocol/name checks, and the host-compiled
battery-smoother test run in a clean clone without a network fetch. It is not a
complete firmware tree and cannot be built or flashed. The upstream MIT license
is vendored at `firmware/LICENSES/BasedHardware-Omi-MIT.txt`.
