#!/usr/bin/env python3
"""Materialize the locked Anticipy source delta. This never builds or flashes."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path
from pathlib import PurePosixPath

from fetch_upstream import validate_checkout


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = FIRMWARE_ROOT.parent
UPSTREAM_LOCK_PATH = FIRMWARE_ROOT / "upstream.lock.json"
REPLACEMENT_LOCK_PATH = FIRMWARE_ROOT / "replacement" / "replacement.lock.json"
TOOLCHAIN_LOCK_PATH = FIRMWARE_ROOT / "replacement" / "toolchain.lock.json"
SOURCE_RECEIPT_NAME = "ANTICIPY_SOURCE_RECEIPT.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_tree_sha256(root: Path) -> str:
    """Hash paths, types, Git-relevant modes, and content deterministically."""

    digest = hashlib.sha256()
    receipt_path = root / SOURCE_RECEIPT_NAME
    paths = sorted(path for path in root.rglob("*") if path != receipt_path)
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            kind = b"L"
            git_mode = b"120000"
            content = path.readlink().as_posix().encode("utf-8")
        elif path.is_dir():
            kind = b"D"
            git_mode = b"040000"
            content = b""
        elif path.is_file():
            kind = b"F"
            executable = bool(path.lstat().st_mode & stat.S_IXUSR)
            git_mode = b"100755" if executable else b"100644"
            content = path.read_bytes()
        else:
            raise RuntimeError(f"unsupported materialized source entry: {path}")
        digest.update(kind)
        digest.update(git_mode)
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def validate_lock_alignment(upstream: dict, replacement: dict) -> None:
    for key in ("repository", "commit", "source_path", "source_tree_git_oid"):
        if replacement["upstream"][key] != upstream[key]:
            raise RuntimeError(f"replacement lock does not match upstream lock: {key}")


def patch_path(replacement: dict) -> Path:
    path = FIRMWARE_ROOT / replacement["patch"]["path"]
    if not path.is_file():
        raise RuntimeError(f"locked source patch is missing: {path}")
    actual = sha256_file(path)
    if actual != replacement["patch"]["sha256"]:
        raise RuntimeError("source patch sha256 does not match replacement lock")
    return path


def export_locked_source_tree(
    source_checkout: Path, source_path: str, destination: Path
) -> None:
    """Export the committed source tree without trusting checkout worktree bytes."""

    source_checkout = source_checkout.resolve()
    destination = destination.resolve()
    completed = subprocess.run(
        ["git", "archive", "--format=tar", f"HEAD:{source_path}"],
        cwd=source_checkout,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or not relative.parts or any(
                part in {"", ".", ".."} for part in relative.parts
            ):
                raise RuntimeError("locked source archive contains an unsafe path")
            target = destination.joinpath(*relative.parts)
            parent = target.parent
            while parent != destination:
                if parent.is_symlink():
                    raise RuntimeError("locked source archive traverses a symlink")
                parent = parent.parent
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise RuntimeError("locked source archive file could not be read")
                target.write_bytes(extracted.read())
                target.chmod(0o755 if member.mode & stat.S_IXUSR else 0o644)
            elif member.issym():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(member.linkname)
            else:
                raise RuntimeError("locked source archive contains an unsupported entry")


def verify_materialized(root: Path, replacement: dict) -> dict[str, str]:
    expected_files = replacement["materialized_source"]["critical_file_sha256"]
    observed_files: dict[str, str] = {}
    for relative, expected in expected_files.items():
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"materialized critical file is missing: {relative}")
        observed = sha256_file(path)
        if observed != expected:
            raise RuntimeError(f"materialized critical file drifted: {relative}")
        observed_files[relative] = observed

    observed_tree = content_tree_sha256(root)
    expected_tree = replacement["materialized_source"]["content_tree_sha256"]
    if observed_tree != expected_tree:
        raise RuntimeError("materialized source content tree does not match lock")
    return observed_files


def apply_locked_patch(destination: Path, replacement: dict) -> None:
    patch = patch_path(replacement)
    destination = destination.resolve()
    try:
        relative_destination = destination.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError("patch destination must stay inside the repository") from exc
    apply_command = [
        "git",
        "apply",
        "--whitespace=nowarn",
        f"--directory={relative_destination.as_posix()}",
        str(patch),
    ]
    subprocess.run(
        apply_command[:2] + ["--check"] + apply_command[2:],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        apply_command,
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def deterministic_receipt(replacement: dict, observed_files: dict[str, str]) -> dict:
    return {
        "schema": 1,
        "status": replacement["status"],
        "upstream": replacement["upstream"],
        "patch": replacement["patch"],
        "materialized_source": {
            "content_tree_sha256": replacement["materialized_source"][
                "content_tree_sha256"
            ],
            "critical_file_sha256": observed_files,
        },
        "toolchain_lock_sha256": sha256_file(TOOLCHAIN_LOCK_PATH),
        "behavior_contract": replacement["behavior_contract"],
        "artifact_built": False,
        "flash_performed": False,
        "physical_hardware_verified": False,
    }


def materialize(source_checkout: Path, destination: Path) -> dict:
    upstream = load_json(UPSTREAM_LOCK_PATH)
    replacement = load_json(REPLACEMENT_LOCK_PATH)
    validate_lock_alignment(upstream, replacement)
    validate_checkout(source_checkout, upstream)
    patch_path(replacement)

    firmware_root = FIRMWARE_ROOT.resolve()
    destination = destination.resolve()
    if firmware_root not in destination.parents:
        raise RuntimeError("destination must stay inside the firmware directory")
    if destination.exists():
        raise RuntimeError("destination already exists; choose a new isolated path")
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = Path(
        tempfile.mkdtemp(prefix=".anticipy-source-", dir=destination.parent)
    ).resolve()
    try:
        export_locked_source_tree(source_checkout, upstream["source_path"], temporary)
        apply_locked_patch(temporary, replacement)
        observed_files = verify_materialized(temporary, replacement)
        receipt = deterministic_receipt(replacement, observed_files)
        receipt_path = temporary / SOURCE_RECEIPT_NAME
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        expected_receipt_sha256 = replacement["materialized_source"][
            "source_receipt_sha256"
        ]
        if sha256_file(receipt_path) != expected_receipt_sha256:
            raise RuntimeError("deterministic source receipt does not match lock")
        temporary.rename(destination)
        return receipt
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=FIRMWARE_ROOT / ".cache" / "omi-v2.0.1-Omi-firmware-v1.0",
        help="locked Omi repository checkout",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=FIRMWARE_ROOT / ".build" / "source" / "anticipy-v2.0.1",
    )
    args = parser.parse_args()
    receipt = materialize(args.source.expanduser().resolve(), args.destination)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
