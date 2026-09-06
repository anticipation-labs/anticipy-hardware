#!/usr/bin/env python3
"""Verify quarantine identity/structure; never pronounce an image flash-safe."""

from __future__ import annotations

import json
import sys
from pathlib import Path


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from uf2 import UF2Error, inspect_uf2  # noqa: E402


def main() -> int:
    quarantine = FIRMWARE_ROOT / "quarantine"
    manifest = json.loads((quarantine / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("classification") != "UNVERIFIED_DO_NOT_FLASH":
        raise SystemExit("refusing: quarantine classification is missing")

    artifact = quarantine / manifest["file"]
    try:
        observed = inspect_uf2(artifact)
    except (OSError, UF2Error) as exc:
        raise SystemExit(f"quarantine verification failed: {exc}") from exc

    expected = {
        "sha256": manifest["sha256"],
        "bytes": manifest["bytes"],
        "blocks": manifest["uf2"]["blocks"],
        "flags": manifest["uf2"]["flags"],
        "family_ids": [manifest["uf2"]["family_id"]],
        "payload_bytes_per_block": manifest["uf2"]["payload_bytes_per_block"],
        "payload_bytes": manifest["uf2"]["payload_bytes"],
        "address_start": manifest["uf2"]["address_start"],
        "address_end_exclusive": manifest["uf2"]["address_end_exclusive"],
    }
    if observed != expected:
        print(json.dumps({"expected": expected, "observed": observed}, indent=2))
        raise SystemExit("quarantine verification failed: manifest mismatch")

    print(
        json.dumps(
            {
                "status": "VERIFIED_QUARANTINE_BYTES_ONLY",
                "flash_approval": False,
                "classification": manifest["classification"],
                "artifact": artifact.name,
                **observed,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
