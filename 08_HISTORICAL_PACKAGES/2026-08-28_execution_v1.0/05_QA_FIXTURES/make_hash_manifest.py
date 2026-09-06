#!/usr/bin/env python3
"""Write deterministic SHA-256 hashes for all released fixture files."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "BUILD_MANIFEST.sha256"
EXCLUDED = {OUTPUT.name}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    files = [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path.name not in EXCLUDED
        and "__pycache__" not in path.parts
    ]
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in sorted(files)]
    OUTPUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} hashes to {OUTPUT.name}")


if __name__ == "__main__":
    main()
