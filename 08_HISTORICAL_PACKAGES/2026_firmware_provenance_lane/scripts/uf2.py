"""Small strict UF2 inspector used by firmware provenance checks."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any


BLOCK_BYTES = 512
MAGIC_START_0 = 0x0A324655
MAGIC_START_1 = 0x9E5D5157
MAGIC_END = 0x0AB16F30
MAX_PAYLOAD_BYTES = 476


class UF2Error(ValueError):
    pass


def inspect_uf2(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if not data or len(data) % BLOCK_BYTES:
        raise UF2Error("UF2 must contain a non-zero whole number of 512-byte blocks")

    records: list[tuple[int, int, int, int, int, int]] = []
    for offset in range(0, len(data), BLOCK_BYTES):
        block = data[offset : offset + BLOCK_BYTES]
        magic0, magic1, flags, address, size, number, total, family = struct.unpack_from(
            "<8I", block, 0
        )
        end_magic = struct.unpack_from("<I", block, BLOCK_BYTES - 4)[0]
        if (magic0, magic1, end_magic) != (MAGIC_START_0, MAGIC_START_1, MAGIC_END):
            raise UF2Error(f"bad UF2 magic in block at byte {offset}")
        if not 0 < size <= MAX_PAYLOAD_BYTES:
            raise UF2Error(f"invalid payload size {size} in block {number}")
        records.append((flags, address, size, number, total, family))

    totals = {record[4] for record in records}
    if totals != {len(records)}:
        raise UF2Error(f"declared block totals do not match file: {sorted(totals)}")
    numbers = [record[3] for record in records]
    if sorted(numbers) != list(range(len(records))) or len(set(numbers)) != len(numbers):
        raise UF2Error("UF2 block numbers are incomplete or duplicated")
    addresses = [record[1] for record in records]
    if len(set(addresses)) != len(addresses):
        raise UF2Error("UF2 target addresses are duplicated")

    payload_sizes = sorted({record[2] for record in records})
    address_start = min(addresses)
    address_end = max(address + size for _, address, size, *_ in records)
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "blocks": len(records),
        "flags": [f"0x{value:08x}" for value in sorted({r[0] for r in records})],
        "family_ids": [f"0x{value:08x}" for value in sorted({r[5] for r in records})],
        "payload_bytes_per_block": payload_sizes,
        "payload_bytes": sum(record[2] for record in records),
        "address_start": f"0x{address_start:08x}",
        "address_end_exclusive": f"0x{address_end:08x}",
    }
