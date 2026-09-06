#!/usr/bin/env python3
"""Fetch the exact audited Omi source commit into an ignored sparse checkout."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = FIRMWARE_ROOT / "upstream.lock.json"


def run(*args: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def validate_checkout(destination: Path, lock: dict) -> None:
    if run("git", "rev-parse", "HEAD", cwd=destination) != lock["commit"]:
        raise RuntimeError("checkout HEAD does not match locked commit")
    source_spec = f"HEAD:{lock['source_path']}"
    if run("git", "rev-parse", source_spec, cwd=destination) != lock["source_tree_git_oid"]:
        raise RuntimeError("source tree object does not match lock")
    license_spec = f"HEAD:{lock['license_path']}"
    if run("git", "rev-parse", license_spec, cwd=destination) != lock["license_blob_git_oid"]:
        raise RuntimeError("license object does not match lock")
    for path, expected_oid in lock["audited_blobs"].items():
        if run("git", "rev-parse", f"HEAD:{path}", cwd=destination) != expected_oid:
            raise RuntimeError(f"audited blob does not match lock: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--destination",
        type=Path,
        default=FIRMWARE_ROOT / ".cache" / "omi-v2.0.1-Omi-firmware-v1.0",
    )
    args = parser.parse_args()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    destination = args.destination.expanduser().resolve()
    firmware_root = FIRMWARE_ROOT.resolve()
    if firmware_root not in destination.parents:
        parser.error("destination must stay inside the firmware directory")

    if destination.exists():
        validate_checkout(destination, lock)
        print(f"verified existing checkout: {destination}")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".omi-fetch-", dir=destination.parent))
    try:
        run("git", "init", "--quiet", str(temporary))
        run("git", "remote", "add", "origin", lock["repository"], cwd=temporary)
        run(
            "git",
            "fetch",
            "--quiet",
            "--depth=1",
            "--filter=blob:none",
            "origin",
            lock["commit"],
            cwd=temporary,
        )
        run("git", "sparse-checkout", "init", "--no-cone", cwd=temporary)
        run(
            "git",
            "sparse-checkout",
            "set",
            f"/{lock['license_path']}",
            f"/{lock['source_path']}/",
            cwd=temporary,
        )
        run("git", "checkout", "--quiet", "--detach", lock["commit"], cwd=temporary)
        validate_checkout(temporary, lock)
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    print(f"fetched and verified locked source: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
