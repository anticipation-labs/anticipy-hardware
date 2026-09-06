#!/usr/bin/env python3
"""Deterministic source/format checks for the Anticipy no-PCB prototype.

These checks do not prove behavior on hardware. They protect the byte-packing,
capacity, pin-map, battery-sense, and BLE-encryption decisions that can be
verified without a XIAO, SD card, motor, or iPhone.
"""

from __future__ import annotations

import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BLOCK_BYTES = 440
FRAME_RATE_HZ = 100
OPUS_BITRATE_BPS = 16_000
CBR_FRAME_BYTES = OPUS_BITRATE_BPS // 8 // FRAME_RATE_HZ
BACKLOG_HOURS = 20
ENGINEERING_MARGIN = 1.15
BATTERY_MAH = 250
RUNTIME_HOURS = 16


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
        frames = [rng.randbytes(rng.randint(1, 255)) for _ in range(count)]
        assert unpack_blocks(pack_frames(frames)) == frames


def check_capacity() -> int:
    # Fixed 16 kb/s produces 20-byte/10-ms frames. The actual writer packs 20
    # framed entries into each 440-byte block, so worst-case storage is 5 blocks/s.
    assert CBR_FRAME_BYTES == 20
    one_second = [bytes([i & 0xFF]) * CBR_FRAME_BYTES for i in range(FRAME_RATE_HZ)]
    bytes_per_second = len(pack_frames(one_second)) * BLOCK_BYTES
    assert bytes_per_second == 2_200
    required = bytes_per_second * 3600 * BACKLOG_HOURS
    required_with_margin = int(required * ENGINEERING_MARGIN)
    assert required == 158_400_000
    assert required_with_margin == 182_160_000
    assert required_with_margin < 1_000_000_000
    return required_with_margin


def check_pin_map() -> None:
    uses = {
        "sd": {"D6", "D8", "D9", "D10"},
        "button": {"D7"},
        "haptic": {"D0"},
    }
    names = list(uses)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            assert uses[left].isdisjoint(uses[right]), (left, right, uses[left] & uses[right])


def firmware_chunks(stream: bytes, att_mtu: int) -> list[bytes]:
    """Model storage.c's negotiated-MTU backlog sender."""
    capacity = att_mtu - 3
    assert capacity >= 2
    chunks: list[bytes] = []
    offset = 0
    while offset < len(stream):
        remaining = len(stream) - offset
        packet_size = min(remaining, BLOCK_BYTES, capacity)
        if remaining > packet_size and remaining - packet_size == 1:
            packet_size -= 1
        assert 1 < packet_size <= capacity
        chunks.append(stream[offset : offset + packet_size])
        offset += packet_size
    return chunks


def check_mtu_backfill_resume() -> None:
    rng = random.Random(0xB1E)
    source_blocks = pack_frames([rng.randbytes(CBR_FRAME_BYTES) for _ in range(2_000)])
    source = b"".join(source_blocks)
    assert len(source) % BLOCK_BYTES == 0

    # 23 is the mandatory default ATT MTU.  185 and 247 are common central
    # outcomes; 296 catches the old protocol's one-byte-control ambiguity; 498
    # exercises this firmware's configured upper limit.
    for att_mtu in (23, 185, 247, 296, 498):
        chunks = firmware_chunks(source, att_mtu)
        assert b"".join(chunks) == source
        assert all(len(chunk) <= att_mtu - 3 for chunk in chunks)
        assert all(len(chunk) != 1 for chunk in chunks)

        for cut in (0, 1, len(chunks) // 2, max(0, len(chunks) - 1)):
            received = b"".join(chunks[:cut])
            committed = len(received) - (len(received) % BLOCK_BYTES)
            resumed = b"".join(firmware_chunks(source[committed:], att_mtu))
            assert source[:committed] + resumed == source


def check_source_contract() -> None:
    main = (ROOT / "src/main.c").read_text()
    codec = (ROOT / "src/codec.c").read_text()
    config_h = (ROOT / "src/config.h").read_text()
    battery = (ROOT / "src/lib/battery/battery.c").read_text()
    sdcard = (ROOT / "src/sdcard.c").read_text()
    storage = (ROOT / "src/storage.c").read_text()
    transport = (ROOT / "src/transport.c").read_text()
    button = (ROOT / "src/button.c").read_text()
    haptic = (ROOT / "src/haptic.c").read_text()
    ios_client = (ROOT / "ios_test_client/AnticipyBLEClient.swift").read_text()
    conf = (ROOT / "prj_xiao_ble_sense_devkitv2-adafruit.conf").read_text()
    overlay = (ROOT / "overlay/xiao_ble_sense_devkitv2-adafruit.overlay").read_text()

    assert "continuing without offline storage" in main
    assert "#define CODEC_OPUS_BITRATE 16000" in config_h
    assert "#define CODEC_OPUS_VBR 0" in config_h
    assert "OPUS_SET_DTX(1)" in codec
    assert "remaining_length -= packet_size;" in storage
    assert "offset += packet_size;" in storage
    assert "bt_gatt_get_mtu(conn)" in storage
    assert "remaining_length - packet_size == 1U" in storage
    assert "return INVALID_OFFSET;" in storage
    assert "storage_is_on = false;" in transport
    assert "current_mtu = info->tx_max_len" not in transport
    assert "current_mtu = bt_gatt_get_mtu(conn)" in transport
    assert "memset(storage_temp_data + buffer_offset, 0" in transport
    assert "flush_partial_storage_record" in transport
    assert "Offline tail could not be finalized before reconnect" in transport
    assert "if (!valid)" in transport
    assert "file_num_array[0] < MAX_STORAGE_BYTES" in transport
    assert "write_current_frame_to_storage" in transport
    assert "transport_clear_offline_audio" in transport
    assert "transport_clear_offline_audio()" in storage
    assert "DT_ALIAS(anticipy_button)" in button
    assert "DT_ALIAS(anticipy_haptic)" in haptic

    assert "gpio1 11 GPIO_ACTIVE_LOW" in overlay  # BFF CS: D6/P1.11
    assert "gpio0 2 GPIO_ACTIVE_HIGH" in overlay  # haptic gate: D0/P0.02
    assert "gpio1 12 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)" in overlay
    assert "sd_en_gpio_pin" not in sdcard
    assert "#define SD_AUDIO_BATCH_BLOCKS 16U" in sdcard
    assert "flush_audio_file_unlocked" in sdcard
    assert "file_num_array[0] = 0;" in sdcard
    assert "if (file_count == 1)" in sdcard
    assert "clear_audio_file(1)" in sdcard

    assert "GPIO_BATTERY_READ_ENABLE, 0" in battery
    assert "GPIO_BATTERY_CHARGING_ENABLE" not in battery
    assert "GPIO_BATTERY_CHARGE_SPEED" not in battery

    assert "CONFIG_BT_SMP=y" in conf
    assert "CONFIG_BT_SMP_SC_PAIR_ONLY=y" in conf
    assert "CONFIG_BT_SMP_SC_ONLY=y" not in conf
    assert "CONFIG_BT_SETTINGS=y" in conf
    assert "bt_conn_set_security(conn, BT_SECURITY_L2)" in transport
    assert "settings_load()" in transport
    for source in (transport, storage, button, haptic):
        assert "BT_GATT_PERM_READ_ENCRYPT" in source or "BT_GATT_PERM_WRITE_ENCRYPT" in source

    assert '30295781-4301-EABD-2904-2849ADFEAE43' in ios_client
    assert '19B10001-E8F2-537E-4F6C-D104768A1214' in ios_client
    assert "static let sdRecordBytes = 440" in ios_client
    assert "try sinkHandle.synchronize()" in ios_client
    assert "committedOffset += UInt32(Self.sdRecordBytes)" in ios_client


def main() -> None:
    check_packing()
    required_with_margin = check_capacity()
    check_pin_map()
    check_mtu_backfill_resume()
    check_source_contract()
    max_average_ma = BATTERY_MAH * 0.85 / RUNTIME_HOURS
    print("PASS: storage packing round-trips 10,000 randomized frames")
    print(f"PASS: 20 h fixed-16-kb/s backlog + 15% = {required_with_margin:,} bytes")
    print("PASS: SD D6/D8/D9/D10, button D7, and haptic D0 do not conflict")
    print("PASS: backlog chunks respect ATT MTU and resume at 440-byte boundaries")
    print("PASS: BLE application characteristics require encryption and bonds persist")
    print("PASS: battery read-enable is LOW; charge-status/current pins are not driven")
    print("PASS: SD batches 16 blocks (~3.2 s active fixed-rate estimate; DTX span needs measurement)")
    print("PASS: current-file offset overrun is rejected and one-file NUKE clears backlog")
    print("PASS: reconnect finalizes the partial SD record; failed live queueing falls back to SD")
    print("BLOCKER: SD audio is plaintext at rest; AES-GCM is not implemented")
    print(f"HARDWARE GATE: 250 mAh 16 h average must be <= {max_average_ma:.2f} mA")


if __name__ == "__main__":
    main()
