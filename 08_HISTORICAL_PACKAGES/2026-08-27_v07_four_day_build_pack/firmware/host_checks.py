#!/usr/bin/env python3
"""Host-side checks for the four-day founder EVT firmware pack.

These checks do not replace a Zephyr build or tests on the assembled device.
They cover the storage-block packing contract, capacity arithmetic, and the
specific source regressions fixed in this pack.
"""

from __future__ import annotations

import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BLOCK_BYTES = 440
FRAME_RATE_HZ = 100
OPUS_BITRATE_BPS = 32_000
BACKLOG_HOURS = 20
ENGINEERING_MARGIN = 1.15


def pack_frames(frames: list[bytes]) -> list[bytes]:
    blocks: list[bytes] = []
    block = bytearray(BLOCK_BYTES)
    offset = 0
    for frame in frames:
        packet_size = len(frame) + 1
        assert 0 < len(frame) <= 255
        assert packet_size <= BLOCK_BYTES
        if offset + packet_size > BLOCK_BYTES:
            blocks.append(bytes(block))
            block = bytearray(BLOCK_BYTES)
            offset = 0
        block[offset] = len(frame)
        block[offset + 1 : offset + packet_size] = frame
        offset += packet_size
        if offset == BLOCK_BYTES:
            blocks.append(bytes(block))
            block = bytearray(BLOCK_BYTES)
            offset = 0
    if offset:
        blocks.append(bytes(block))
    return blocks


def unpack_blocks(blocks: list[bytes]) -> list[bytes]:
    frames: list[bytes] = []
    for block in blocks:
        assert len(block) == BLOCK_BYTES
        offset = 0
        while offset < len(block):
            size = block[offset]
            if size == 0:
                break
            end = offset + 1 + size
            assert end <= len(block)
            frames.append(block[offset + 1 : end])
            offset = end
    return frames


def check_packing() -> None:
    rng = random.Random(0xA71C1)
    for count in (1, 10, 100, 10_000):
        frames = [rng.randbytes(rng.randint(18, 80)) for _ in range(count)]
        assert unpack_blocks(pack_frames(frames)) == frames


def check_capacity() -> None:
    payload_bytes_per_second = OPUS_BITRATE_BPS / 8
    framing_bytes_per_second = FRAME_RATE_HZ
    required = (payload_bytes_per_second + framing_bytes_per_second) * 3600 * BACKLOG_HOURS
    required_with_margin = required * ENGINEERING_MARGIN
    assert required_with_margin < 350_000_000
    assert required_with_margin < 1_000_000_000  # even a 1 GB FAT card clears the target


def check_pin_map() -> None:
    # Official XIAO nRF52840 Sense / Adafruit Audio BFF mapping.
    uses = {
        "sd": {"D0", "D8", "D9", "D10"},
        "button": {"D7"},
        "haptic": {"D6"},
        "speaker_bus_present_but_speaker_omitted": {"D1", "D2", "D3"},
        "imu_i2c_reserved": {"D4", "D5"},
    }
    names = list(uses)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            assert uses[left].isdisjoint(uses[right]), (left, right, uses[left] & uses[right])


def check_regressions() -> None:
    main = (ROOT / "src/main.c").read_text()
    sdcard = (ROOT / "src/sdcard.c").read_text()
    storage = (ROOT / "src/storage.c").read_text()
    transport = (ROOT / "src/transport.c").read_text()
    button = (ROOT / "src/button.c").read_text()
    overlay = (ROOT / "overlay/xiao_ble_sense_devkitv2-adafruit.overlay").read_text()

    assert "continuing without offline storage" in main
    assert "int rc = create_file(header);\n    k_free(header);" in sdcard
    assert "remaining_length -= packet_size;" in storage
    assert "offset += packet_size;" in storage
    assert "storage_is_on = false;" in transport
    assert "memset(storage_temp_data + buffer_offset, 0" in transport
    assert "DT_ALIAS(anticipy_button)" in button
    assert "D4 Pin" not in button and "D5 Pin" not in button
    assert "gpio1 12 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)" in overlay


def main() -> None:
    check_packing()
    check_capacity()
    check_pin_map()
    check_regressions()
    max_average_ma = 500 * 0.85 / 16
    print("PASS: storage packing round-trips through 10,000 randomized frames")
    print("PASS: 20 h backlog + 15% margin is under 350 MB")
    print("PASS: SD, D7 button, D6 haptic, Audio BFF, and reserved IMU I2C pins do not conflict")
    print("PASS: critical source fixes are present")
    print(f"HARDWARE GATE: measured 16 h average must be <= {max_average_ma:.2f} mA")


if __name__ == "__main__":
    main()
