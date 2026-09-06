#!/usr/bin/env python3
"""Probe or build the locked Anticipy firmware candidate. This never flashes."""

from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from fetch_upstream import validate_checkout
from materialize_replacement import (
    REPLACEMENT_LOCK_PATH,
    SOURCE_RECEIPT_NAME,
    TOOLCHAIN_LOCK_PATH,
    UPSTREAM_LOCK_PATH,
    deterministic_receipt,
    load_json,
    materialize,
    patch_path,
    sha256_file,
    validate_lock_alignment,
    verify_materialized,
)
from spdx_sbom import (
    SPDX_FILENAME,
    deterministic_spdx_sbom,
    reject_symlink_ancestors,
    sbom_readiness,
    validate_artifact_inventory,
    write_validated_spdx,
)


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOOLS = ("west", "cmake", "ninja")
COMPILER_CANDIDATES = ("arm-zephyr-eabi-gcc", "arm-none-eabi-gcc")
TOOLCHAIN_DECLARATION_ENV = "ANTICIPY_TOOLCHAIN_IMAGE_DIGEST"
CONTAINER_PROVENANCE = "UNVERIFIED_OPERATOR_DECLARATION"
ACTIVE_PROJECTS_FILENAME = "west-active-projects-frozen.tsv"
_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def command_output(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_json_sha256(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )


def source_status(source: Path, upstream: dict, replacement: dict) -> tuple[bool, str]:
    try:
        validate_lock_alignment(upstream, replacement)
        validate_checkout(source, upstream)
        patch_path(replacement)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        return False, str(exc)
    return True, "locked upstream and Anticipy patch verified"


def require_repository_root(path: Path) -> None:
    expected = path.resolve()
    observed = Path(command_output("git", "rev-parse", "--show-toplevel", cwd=path)).resolve()
    if observed != expected:
        raise RuntimeError(
            f"west project is not a Git worktree root: {expected} "
            f"(git resolved {observed})"
        )


def repository_head(path: Path) -> str:
    require_repository_root(path)
    return command_output("git", "rev-parse", "HEAD", cwd=path)


def repository_dirty(path: Path) -> str:
    require_repository_root(path)
    return command_output(
        "git",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
        cwd=path,
    )


def canonical_project_path(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or any(character.isspace() for character in value)
        or any(ord(character) < 0x20 for character in value)
    ):
        raise RuntimeError("west project path must use printable POSIX separators")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value in {".", ".."}
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
        or path.parts[0] == ".west"
    ):
        raise RuntimeError("west project path must be relative, normalized, and safe")
    return value


def canonical_repository_url(value: object) -> str:
    if not isinstance(value, str) or not value or any(
        character.isspace() or ord(character) < 0x20 for character in value
    ):
        raise RuntimeError("west project repository must be a printable URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(
            "west project repository must be credential-free canonical HTTPS"
        )
    return value


def canonical_active_projects_tsv(projects: dict[str, str]) -> bytes:
    if not isinstance(projects, dict) or not projects:
        raise RuntimeError("active west project set must be a non-empty object")
    normalized: dict[str, str] = {}
    for raw_path, raw_commit in projects.items():
        path = canonical_project_path(raw_path)
        if path in normalized:
            raise RuntimeError("active west project set contains a duplicate path")
        if not isinstance(raw_commit, str) or not _GIT_COMMIT.fullmatch(raw_commit):
            raise RuntimeError(
                "active west project HEAD must be 40-character lowercase hexadecimal"
            )
        normalized[path] = raw_commit
    if "nrf" not in normalized:
        raise RuntimeError("active west project set must include nrf")
    return "".join(
        f"{path}\t{normalized[path]}\n" for path in sorted(normalized)
    ).encode("utf-8")


def active_west_projects(
    west: str, workspace: Path, ncs_repository: str
) -> tuple[dict[str, str], dict[str, str], list[str]]:
    """Return only West's active projects; never request or inspect inactive ones."""

    completed = subprocess.run(
        [west, "list", "-f", "{path}\t{abspath}\t{url}"],
        cwd=workspace,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if "\r" in completed.stdout:
        raise RuntimeError("west active project listing contains non-canonical lines")

    commits: dict[str, str] = {}
    repositories: dict[str, str] = {}
    failures: list[str] = []

    def add_project(path: str, absolute: Path, repository: str) -> None:
        path = canonical_project_path(path)
        if path in commits:
            raise RuntimeError("west active project listing contains a duplicate path")
        expected = workspace / Path(*PurePosixPath(path).parts)
        if absolute != expected or absolute.resolve() != expected:
            raise RuntimeError("west active project path is unsafe or inconsistent")
        commits[path] = repository_head(absolute)
        repositories[path] = canonical_repository_url(repository)
        if repository_dirty(absolute):
            failures.append(f"dirty west project: {path}")

    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 3:
            raise RuntimeError("west active project listing is malformed")
        raw_path, raw_absolute, repository = fields
        absolute = Path(raw_absolute)
        if not absolute.is_absolute():
            raise RuntimeError("west active project absolute path is malformed")
        add_project(
            raw_path,
            absolute,
            ncs_repository if raw_path == "nrf" else repository,
        )
    if "nrf" not in commits:
        add_project("nrf", workspace / "nrf", ncs_repository)

    canonical_active_projects_tsv(commits)
    return (
        dict(sorted(commits.items())),
        dict(sorted(repositories.items())),
        failures,
    )


def _locked_board_status(zephyr: Path, toolchain: dict) -> tuple[dict[str, object], list[str]]:
    locked = toolchain["candidate_build"]["board_definition"]
    relative_root = locked["zephyr_path"]
    if relative_root != "boards/arm/xiao_ble":
        raise RuntimeError("locked board definition path is not the reviewed XIAO BLE tree")
    board_root = (zephyr / relative_root).resolve()
    if zephyr.resolve() not in board_root.parents or not board_root.is_dir():
        raise RuntimeError("locked board definition directory is missing or unsafe")

    observed_tree = command_output(
        "git", "rev-parse", f"HEAD:{relative_root}", cwd=zephyr
    )
    expected_files = locked["critical_file_sha256"]
    if not isinstance(expected_files, dict) or not expected_files:
        raise RuntimeError("locked board definition has no critical files")
    observed_files: dict[str, str] = {}
    failures: list[str] = []
    for relative, expected_digest in sorted(expected_files.items()):
        if Path(relative).name != relative:
            raise RuntimeError("locked board definition filename is unsafe")
        path = board_root / relative
        if not path.is_file():
            failures.append(f"locked board definition file missing: {relative}")
            continue
        observed = sha256_file(path)
        observed_files[relative] = observed
        if observed != expected_digest:
            failures.append(f"locked board definition file mismatch: {relative}")
    if observed_tree != locked["git_tree_oid"]:
        failures.append("locked board definition Git tree mismatch")
    return {
        "board_definition_git_tree_oid": observed_tree,
        "board_definition_file_sha256": observed_files,
    }, failures


def _cmake_cache_entries(
    output: Path, required_keys: set[str]
) -> dict[str, dict[str, str]]:
    cache = output / "CMakeCache.txt"
    try:
        metadata = cache.lstat()
    except OSError as exc:
        raise RuntimeError("CMake cache is missing or unreadable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("CMake cache is not a regular file")

    entries: dict[str, dict[str, str]] = {}
    forbidden_keys = {"BOARD_ALIAS", "BOARD_DEPRECATED"}
    for line in cache.read_text(encoding="utf-8", errors="strict").splitlines():
        if "=" not in line or ":" not in line.split("=", 1)[0]:
            continue
        key_and_type, value = line.split("=", 1)
        key, cache_type = key_and_type.split(":", 1)
        if key in forbidden_keys:
            raise RuntimeError(f"CMake cache remapped the locked board through {key}")
        if key not in required_keys:
            continue
        if key in entries:
            raise RuntimeError(f"CMake cache repeats required key: {key}")
        if not cache_type or any(ord(character) < 0x20 for character in value):
            raise RuntimeError(f"CMake cache has an unsafe required entry: {key}")
        entries[key] = {"type": cache_type, "value": value}

    missing = sorted(required_keys - entries.keys())
    if missing:
        raise RuntimeError(f"CMake cache is missing required keys: {', '.join(missing)}")
    return entries


def _locked_toolchain_prefix(toolchain: dict) -> Path:
    runtime = toolchain.get("toolchain_container", {}).get("runtime_toolchain")
    if not isinstance(runtime, dict):
        raise RuntimeError("locked runtime toolchain metadata is missing")
    prefix_value = runtime.get("selected_prefix")
    if (
        not isinstance(prefix_value, str)
        or not prefix_value
        or any(ord(character) < 0x20 for character in prefix_value)
    ):
        raise RuntimeError("locked Nordic toolchain prefix is invalid")
    prefix = Path(prefix_value)
    if not prefix.is_absolute() or ".." in prefix.parts:
        raise RuntimeError("locked Nordic toolchain prefix is unsafe")
    return prefix


def _locked_tool_paths(toolchain: dict) -> dict[str, str]:
    prefix = _locked_toolchain_prefix(toolchain)
    arm_bin = prefix / "opt" / "zephyr-sdk" / "arm-zephyr-eabi" / "bin"
    return {
        "west": str(prefix / "usr" / "local" / "bin" / "west"),
        "cmake": str(prefix / "usr" / "local" / "bin" / "cmake"),
        "ninja": str(prefix / "usr" / "local" / "bin" / "ninja"),
        "arm_compiler": str(arm_bin / "arm-zephyr-eabi-gcc"),
    }


def _expected_cmake_inputs(
    toolchain: dict,
    application_source: Path,
    ncs_workspace: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, str], dict[str, object]]:
    prefix = _locked_toolchain_prefix(toolchain)
    sdk = prefix / "opt" / "zephyr-sdk"
    arm_bin = sdk / "arm-zephyr-eabi" / "bin"
    python = prefix / "usr" / "local" / "bin" / "python3.8"
    zephyr_base = (ncs_workspace / "zephyr").resolve()
    board = toolchain["candidate_build"]["board"]
    board_dir = (
        zephyr_base
        / toolchain["candidate_build"]["board_definition"]["zephyr_path"]
    ).resolve()
    configuration = toolchain["candidate_build"]["configuration_file"]
    overlay = toolchain["candidate_build"]["devicetree_overlay"]
    application_source = application_source.resolve()

    entries = {
        "BOARD": {"type": "STRING", "value": board},
        "BOARD_DIR": {"type": "PATH", "value": str(board_dir)},
        "CACHED_BOARD": {"type": "STRING", "value": board},
        "CACHED_CONF_FILE": {"type": "STRING", "value": configuration},
        "CMAKE_ASM_COMPILER": {
            "type": "FILEPATH",
            "value": str(arm_bin / "arm-zephyr-eabi-gcc"),
        },
        "CMAKE_COMMAND": {
            "type": "INTERNAL",
            "value": str(prefix / "usr" / "local" / "bin" / "cmake"),
        },
        "CMAKE_CXX_COMPILER": {
            "type": "STRING",
            "value": str(arm_bin / "arm-zephyr-eabi-g++"),
        },
        "CMAKE_C_COMPILER": {
            "type": "STRING",
            "value": str(arm_bin / "arm-zephyr-eabi-gcc"),
        },
        "CMAKE_HOME_DIRECTORY": {
            "type": "INTERNAL",
            "value": str(application_source),
        },
        "CMAKE_MAKE_PROGRAM": {
            "type": "FILEPATH",
            "value": str(prefix / "usr" / "local" / "bin" / "ninja"),
        },
        "DTC_OVERLAY_FILE": {"type": "STRING", "value": overlay},
        "WEST": {
            "type": "INTERNAL",
            "value": f"{python};-m;west",
        },
        "WEST_PYTHON": {"type": "UNINITIALIZED", "value": str(python)},
        "ZEPHYR_BASE": {"type": "PATH", "value": str(zephyr_base)},
        "ZEPHYR_SDK_INSTALL_DIR": {"type": "INTERNAL", "value": str(sdk)},
        "ZEPHYR_TOOLCHAIN_VARIANT": {"type": "INTERNAL", "value": "zephyr"},
        "Zephyr-sdk_DIR": {"type": "PATH", "value": str(sdk / "cmake")},
    }
    resolved_paths = {
        "BOARD_DIR": str(board_dir),
        "CACHED_CONF_FILE": str(application_source / configuration),
        "CMAKE_HOME_DIRECTORY": str(application_source),
        "DTC_OVERLAY_FILE": str(application_source / overlay),
        "ZEPHYR_BASE": str(zephyr_base),
    }
    expected = {
        "application_source": str(application_source),
        "board": board,
        "board_dir": str(board_dir),
        "configuration_file": str(application_source / configuration),
        "devicetree_overlay": str(application_source / overlay),
        "toolchain_prefix": str(prefix),
        "zephyr_base": str(zephyr_base),
    }
    return entries, resolved_paths, expected


def ncs_status(
    workspace: Path, toolchain: dict, west: str | None
) -> tuple[bool, dict]:
    expected_ncs = toolchain["nrf_connect_sdk"]
    expected_zephyr = toolchain["zephyr"]
    details: dict[str, object] = {
        "workspace": str(workspace),
        "ncs_commit": None,
        "zephyr_commit": None,
        "west_manifest_sha256": None,
        "west_config_sha256": None,
        "active_projects_frozen_filename": ACTIVE_PROJECTS_FILENAME,
        "active_projects_frozen_sha256": None,
        "active_projects_frozen_project_count": 0,
        "project_commits_sha256": None,
        "project_commits": {},
        "project_repositories_sha256": None,
        "project_repositories": {},
        "project_count": 0,
        "board_definition_git_tree_oid": None,
        "board_definition_file_sha256": {},
    }
    failures: list[str] = []
    try:
        workspace = workspace.resolve()
        if west is None:
            raise RuntimeError("west executable is unavailable")
        config_path = workspace / ".west" / "config"
        if not config_path.is_file():
            raise RuntimeError("workspace has no .west/config")
        details["west_config_sha256"] = sha256_file(config_path)

        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")
        manifest_path = config.get("manifest", "path", fallback=None)
        manifest_file = config.get("manifest", "file", fallback="west.yml")
        if manifest_path != "nrf" or manifest_file != "west.yml":
            raise RuntimeError(".west manifest must be exactly nrf/west.yml")

        nrf_root = workspace / "nrf"
        nrf_head = repository_head(nrf_root)
        if not _GIT_COMMIT.fullmatch(nrf_head):
            raise RuntimeError(
                "active west project HEAD must be 40-character lowercase hexadecimal"
            )
        if nrf_head != expected_ncs["commit"]:
            raise RuntimeError("NCS commit mismatch before active project discovery")
        if repository_dirty(nrf_root):
            raise RuntimeError(
                "dirty west project: nrf; refusing active project discovery"
            )
        details["west_manifest_sha256"] = sha256_file(nrf_root / "west.yml")
        if details["west_manifest_sha256"] != expected_ncs["west_manifest_sha256"]:
            raise RuntimeError(
                "NCS west.yml mismatch before active project discovery"
            )

        observed_topdir = Path(command_output(west, "topdir", cwd=workspace)).resolve()
        if observed_topdir != workspace:
            failures.append("west topdir does not match the requested workspace")

        commits, repositories, active_failures = active_west_projects(
            west,
            workspace,
            toolchain["nrf_connect_sdk"]["repository"],
        )
        failures.extend(active_failures)
        details["project_commits"] = commits
        details["project_count"] = len(commits)
        details["project_commits_sha256"] = canonical_json_sha256(
            details["project_commits"]
        )
        details["project_repositories"] = repositories
        details["project_repositories_sha256"] = canonical_json_sha256(repositories)
        active_snapshot = canonical_active_projects_tsv(commits)
        details["active_projects_frozen_sha256"] = sha256_bytes(active_snapshot)
        details["active_projects_frozen_project_count"] = len(commits)
        details["ncs_commit"] = commits.get("nrf")
        details["zephyr_commit"] = commits.get("zephyr")
        board_detail, board_failures = _locked_board_status(
            workspace / "zephyr", toolchain
        )
        details.update(board_detail)
        failures.extend(board_failures)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        details["detail"] = str(exc)
        return False, details

    if details["ncs_commit"] != expected_ncs["commit"]:
        failures.append("NCS commit mismatch")
    if details["zephyr_commit"] != expected_zephyr["commit"]:
        failures.append("Zephyr commit mismatch")
    if details["west_manifest_sha256"] != expected_ncs["west_manifest_sha256"]:
        failures.append("NCS west.yml mismatch")
    details["detail"] = (
        "; ".join(failures)
        if failures
        else (
            "all active west projects present and clean; canonical active-project "
            "snapshot and locked NCS sources verified"
        )
    )
    return not failures, details


def tool_paths() -> tuple[dict[str, str | None], str | None]:
    tools = {name: shutil.which(name) for name in REQUIRED_TOOLS}
    compiler = next(
        (
            path
            for name in COMPILER_CANDIDATES
            if (path := shutil.which(name)) is not None
        ),
        None,
    )
    tools["arm_compiler"] = compiler
    return tools, compiler


def tool_versions(tools: dict[str, str | None]) -> dict[str, str]:
    versions: dict[str, str] = {}
    arguments = {
        "west": ("--version",),
        "cmake": ("--version",),
        "ninja": ("--version",),
        "arm_compiler": ("--version",),
    }
    for name, path in tools.items():
        if path:
            output = command_output(path, *arguments[name])
            versions[name] = output.splitlines()[0]
    return versions


def locked_source_date_epoch(source: Path, source_receipt: dict) -> int:
    commit = source_receipt.get("upstream", {}).get("commit")
    if not isinstance(commit, str):
        raise RuntimeError("source receipt has no locked upstream commit")
    value = command_output(
        "git", "show", "-s", "--format=%ct", commit, cwd=source
    )
    if not value.isascii() or not value.isdecimal():
        raise RuntimeError("locked source commit timestamp is invalid")
    epoch = int(value)
    if epoch < 0:
        raise RuntimeError("locked source commit timestamp is invalid")
    return epoch


def probe(source: Path, ncs_workspace: Path) -> dict:
    upstream = load_json(UPSTREAM_LOCK_PATH)
    replacement = load_json(REPLACEMENT_LOCK_PATH)
    toolchain = load_json(TOOLCHAIN_LOCK_PATH)
    tools, compiler = tool_paths()
    expected_tools = _locked_tool_paths(toolchain)
    tool_paths_match = tools == expected_tools
    source_ok, source_detail = source_status(source, upstream, replacement)
    ncs_ok, ncs_detail = ncs_status(ncs_workspace, toolchain, tools["west"])
    sbom_ok, sbom_detail = sbom_readiness()
    expected_digest = toolchain["toolchain_container"]["digest"]
    declaration_present = TOOLCHAIN_DECLARATION_ENV in os.environ
    declaration_matches = os.environ.get(TOOLCHAIN_DECLARATION_ENV) == expected_digest
    ready = (
        source_ok
        and ncs_ok
        and all(tools[name] for name in REQUIRED_TOOLS)
        and bool(compiler)
        and tool_paths_match
        and declaration_matches
        and sbom_ok
    )
    return {
        "status": "PINNED_CANDIDATE_BUILD_ENVIRONMENT_ONLY",
        "ready": ready,
        "source": {
            "checkout": str(source),
            "verified": source_ok,
            "detail": source_detail,
        },
        "ncs": {"verified": ncs_ok, **ncs_detail},
        "tools": tools,
        "expected_tools": expected_tools,
        "tool_paths_match": tool_paths_match,
        "sbom": sbom_detail,
        "toolchain_container": {
            "expected_digest": expected_digest,
            "declaration_env": TOOLCHAIN_DECLARATION_ENV,
            "declaration_present": declaration_present,
            "declaration_matches": declaration_matches,
            "provenance": CONTAINER_PROVENANCE,
            "warning": "this process cannot independently prove its OCI image identity",
        },
        "artifact_built": False,
        "flash_approved": False,
        "flash_performed": False,
    }


def ensure_materialized(source: Path, destination: Path) -> dict:
    replacement = load_json(REPLACEMENT_LOCK_PATH)
    if not destination.exists():
        return materialize(source, destination)
    observed = verify_materialized(destination, replacement)
    expected_receipt = deterministic_receipt(replacement, observed)
    receipt_path = destination / SOURCE_RECEIPT_NAME
    if not receipt_path.is_file():
        raise RuntimeError("existing materialized source receipt is missing or drifted")
    receipt_bytes = receipt_path.read_bytes()
    expected_receipt_sha256 = replacement["materialized_source"][
        "source_receipt_sha256"
    ]
    if sha256_bytes(receipt_bytes) != expected_receipt_sha256:
        raise RuntimeError("existing materialized source receipt hash is drifted")
    if json.loads(receipt_bytes) != expected_receipt:
        raise RuntimeError("existing materialized source receipt is missing or drifted")
    return expected_receipt


def hash_artifacts(output: Path) -> dict[str, dict[str, object]]:
    output = reject_symlink_ancestors(output, "firmware artifact output")
    if not output.is_dir():
        raise RuntimeError("firmware artifact output is missing or not a directory")
    zephyr = reject_symlink_ancestors(output / "zephyr", "firmware artifact directory")
    if not zephyr.exists():
        return {}
    if not zephyr.is_dir():
        raise RuntimeError("firmware artifact directory is not a directory")

    candidates: dict[str, tuple[Path, int]] = {}
    for suffix in ("elf", "hex", "bin", "uf2", "map"):
        path = reject_symlink_ancestors(
            zephyr / f"zephyr.{suffix}", f"firmware artifact zephyr.{suffix}"
        )
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise RuntimeError(f"cannot inspect firmware artifact: {path.name}") from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"firmware artifact is not a regular file: {path.name}")
        candidates[path.name] = (path, metadata.st_size)

    artifacts: dict[str, dict[str, object]] = {}
    for name, (path, size) in candidates.items():
        artifacts[name] = {
            "bytes": size,
            "sha256": sha256_file(path),
        }
    return artifacts


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clear_reserved_sbom_outputs(output: Path) -> bool:
    """Remove reserved SBOM files and report whether the build contaminated them."""

    output = reject_symlink_ancestors(output, "candidate build output")
    if output.exists() and not output.is_dir():
        raise RuntimeError("candidate build output is not a directory")
    contaminated = False
    reserved = (
        output / SPDX_FILENAME,
        output / f".{SPDX_FILENAME}.tmp",
    )
    for path in reserved:
        if path.is_symlink() or path.is_file():
            path.unlink()
            contaminated = True
        elif path.exists():
            raise RuntimeError("reserved SBOM output is not a removable regular file")
    return contaminated


def write_active_projects_snapshot(path: Path, content: bytes) -> dict[str, object]:
    path = reject_symlink_ancestors(path, "active west project snapshot")
    if path.exists():
        raise RuntimeError(
            "build contaminated the reserved active west project snapshot path"
        )
    path.write_bytes(content)
    return validate_active_projects_snapshot(path, content)


def validate_active_projects_snapshot(
    path: Path, expected_content: bytes
) -> dict[str, object]:
    path = reject_symlink_ancestors(path, "active west project snapshot")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeError(
            "active west project snapshot is missing or unreadable"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("active west project snapshot is not a regular file")
    observed = path.read_bytes()
    if observed != expected_content:
        raise RuntimeError("active west project snapshot bytes drifted after write")
    return {
        "path": ACTIVE_PROJECTS_FILENAME,
        "sha256": sha256_bytes(observed),
        "project_count": len(observed.splitlines()),
    }


def build(
    source: Path,
    materialized_source: Path,
    ncs_workspace: Path,
    output: Path,
    status: dict,
) -> dict:
    if not status["ready"]:
        raise RuntimeError("environment does not satisfy every pinned build input")
    firmware_root = FIRMWARE_ROOT.resolve()
    output = reject_symlink_ancestors(output, "candidate build output")
    if firmware_root not in output.resolve().parents:
        raise RuntimeError("output must stay inside the firmware directory")
    if firmware_root not in materialized_source.resolve().parents:
        raise RuntimeError("materialized source must stay inside the firmware directory")
    if output.exists():
        raise RuntimeError("output already exists; choose a new isolated output path")

    source_receipt = ensure_materialized(source, materialized_source)
    source_date_epoch = locked_source_date_epoch(source, source_receipt)
    toolchain = load_json(TOOLCHAIN_LOCK_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)

    west = status["tools"]["west"]
    active_snapshot_bytes = canonical_active_projects_tsv(
        status["ncs"]["project_commits"]
    )
    active_snapshot_sha256 = sha256_bytes(active_snapshot_bytes)
    if (
        active_snapshot_sha256
        != status["ncs"]["active_projects_frozen_sha256"]
        or len(status["ncs"]["project_commits"])
        != status["ncs"]["active_projects_frozen_project_count"]
    ):
        raise RuntimeError(
            "active west project snapshot changed after the readiness probe"
        )
    versions = tool_versions(status["tools"])
    expected_zephyr_base = (ncs_workspace / "zephyr").resolve()
    expected_application_source = materialized_source.resolve()
    (
        expected_cache_entries,
        expected_cache_paths,
        expected_cmake_receipt,
    ) = _expected_cmake_inputs(
        toolchain,
        expected_application_source,
        ncs_workspace,
    )
    command = [
        west,
        "build",
        "--pristine",
        "-b",
        toolchain["candidate_build"]["board"],
        "-d",
        str(output),
        str(materialized_source),
        "--",
        f"-DZEPHYR_BASE:PATH={expected_zephyr_base}",
        f"-DCONF_FILE:STRING={toolchain['candidate_build']['configuration_file']}",
        f"-DDTC_OVERLAY_FILE:STRING={toolchain['candidate_build']['devicetree_overlay']}",
    ]
    build_environment = os.environ.copy()
    build_environment["SOURCE_DATE_EPOCH"] = str(source_date_epoch)
    completed = subprocess.run(
        command,
        cwd=ncs_workspace,
        env=build_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    reject_symlink_ancestors(output, "candidate build output")
    output.mkdir(parents=True, exist_ok=True)
    reject_symlink_ancestors(output, "candidate build output")
    log_path = output / "build.log"
    log_path.write_text(completed.stdout, encoding="utf-8")
    active_snapshot_path = output / ACTIVE_PROJECTS_FILENAME
    active_snapshot_record = write_active_projects_snapshot(
        active_snapshot_path, active_snapshot_bytes
    )
    reserved_sbom_contamination = clear_reserved_sbom_outputs(output)

    required_cache_keys = set(expected_cache_entries)
    observed_cache_entries: dict[str, dict[str, str]] = {}
    observed_cache_paths: dict[str, str | None] = {
        key: None
        for key in (
            "BOARD_DIR",
            "CACHED_CONF_FILE",
            "CMAKE_HOME_DIRECTORY",
            "DTC_OVERLAY_FILE",
            "ZEPHYR_BASE",
        )
    }
    cmake_inputs_error: str | None = None
    try:
        observed_cache_entries = _cmake_cache_entries(output, required_cache_keys)
        observed_cache_paths = expected_cache_paths
        cmake_inputs_verified = observed_cache_entries == expected_cache_entries
        if not cmake_inputs_verified:
            cmake_inputs_error = "CMake cache does not match every locked build input"
    except (OSError, RuntimeError, UnicodeError) as exc:
        cmake_inputs_verified = False
        cmake_inputs_error = str(exc)

    post_ok, post_ncs = ncs_status(ncs_workspace, toolchain, west)
    sdk_unchanged = (
        post_ok
        and post_ncs["project_commits_sha256"]
        == status["ncs"]["project_commits_sha256"]
        and post_ncs["active_projects_frozen_sha256"]
        == status["ncs"]["active_projects_frozen_sha256"]
        and post_ncs["active_projects_frozen_project_count"]
        == status["ncs"]["active_projects_frozen_project_count"]
        and post_ncs["project_repositories_sha256"]
        == status["ncs"]["project_repositories_sha256"]
        and post_ncs["west_manifest_sha256"]
        == status["ncs"]["west_manifest_sha256"]
        and post_ncs["west_config_sha256"] == status["ncs"]["west_config_sha256"]
    )
    artifact_error: str | None = None
    try:
        artifacts = hash_artifacts(output)
    except (OSError, RuntimeError) as exc:
        artifacts = {}
        artifact_error = str(exc)
    artifact_built = completed.returncode == 0 and bool(artifacts)
    build_invariants_passed = (
        completed.returncode == 0
        and "zephyr.uf2" in artifacts
        and sdk_unchanged
        and cmake_inputs_verified
        and not reserved_sbom_contamination
        and artifact_error is None
    )
    sbom_record: dict[str, object] | None = None
    sbom_error: str | None = None
    sbom_path = output / SPDX_FILENAME
    if build_invariants_passed:
        try:
            spdx_document = deterministic_spdx_sbom(
                artifact_root=output,
                artifacts=artifacts,
                replacement=load_json(REPLACEMENT_LOCK_PATH),
                source_receipt=source_receipt,
                source_receipt_sha256=sha256_file(
                    materialized_source / SOURCE_RECEIPT_NAME
                ),
                toolchain=toolchain,
                toolchain_lock_sha256=sha256_file(TOOLCHAIN_LOCK_PATH),
                pre_ncs=status["ncs"],
                post_ncs=post_ncs,
                active_projects_path=active_snapshot_path,
                container_declaration_matched=status["toolchain_container"][
                    "declaration_matches"
                ],
                source_date_epoch=source_date_epoch,
            )
            sbom_record = write_validated_spdx(sbom_path, spdx_document)
            validate_artifact_inventory(output, artifacts)
            if sha256_file(sbom_path) != sbom_record["sha256"]:
                raise RuntimeError("SBOM SHA-256 drifted after artifact recheck")
            final_snapshot_record = validate_active_projects_snapshot(
                active_snapshot_path, active_snapshot_bytes
            )
            if final_snapshot_record != active_snapshot_record:
                raise RuntimeError(
                    "active west project snapshot record drifted during final checks"
                )
            active_snapshot_record = final_snapshot_record
        except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
            clear_reserved_sbom_outputs(output)
            sbom_record = None
            sbom_error = str(exc)
    else:
        sbom_error = (
            "build produced a reserved SBOM output"
            if reserved_sbom_contamination
            else (
                f"firmware artifact discovery failed: {artifact_error}"
                if artifact_error is not None
                else "build, artifact, or immutable SDK invariants did not pass"
            )
        )
        clear_reserved_sbom_outputs(output)
    candidate_accepted = build_invariants_passed and sbom_record is not None
    receipt = {
        "schema": 1,
        "status": (
            "CANDIDATE_BUILD_SUCCEEDED_NOT_FLASH_APPROVED"
            if candidate_accepted
            else "CANDIDATE_BUILD_OR_PROVENANCE_FAILED"
        ),
        "build_exit_code": completed.returncode,
        "candidate_accepted": candidate_accepted,
        "source_receipt_sha256": sha256_file(materialized_source / SOURCE_RECEIPT_NAME),
        "source": source_receipt,
        "toolchain": {
            "lock_sha256": sha256_file(TOOLCHAIN_LOCK_PATH),
            "expected_container_digest": toolchain["toolchain_container"]["digest"],
            "container_declaration_matched": status["toolchain_container"][
                "declaration_matches"
            ],
            "container_provenance": CONTAINER_PROVENANCE,
            "container_warning": (
                "receipt does not independently prove which OCI image executed the build"
            ),
            "pre_build_ncs": status["ncs"],
            "post_build_ncs": {"verified": post_ok, **post_ncs},
            "sdk_unchanged_during_build": sdk_unchanged,
            "west_active_projects_frozen": active_snapshot_record,
            "nrf_west_yml_sha256": status["ncs"]["west_manifest_sha256"],
            "west_config_sha256": status["ncs"]["west_config_sha256"],
            "source_date_epoch": source_date_epoch,
            "versions": versions,
            "cmake_inputs": {
                "expected": expected_cmake_receipt,
                "observed_cache_entries": observed_cache_entries,
                "observed_resolved_paths": observed_cache_paths,
                "detail": cmake_inputs_error or "all locked CMake inputs verified",
                "verified": cmake_inputs_verified,
            },
        },
        "command": command,
        "command_shell_display": shlex.join(command),
        "build_log_sha256": sha256_file(log_path),
        "artifacts": artifacts,
        "sbom": (
            sbom_record
            if sbom_record is not None
            else {"status": "NOT_EMITTED", "detail": sbom_error}
        ),
        "artifact_built": artifact_built,
        "flash_approved": False,
        "flash_performed": False,
        "security_release_blockers": [
            "container execution identity is not independently attested",
            "active west project snapshot is build evidence, not signed attestation",
            "no Anticipy-owned signed boot/update chain",
            "no rollback protection",
            "no authenticated owner enrollment and encrypted GATT policy",
            "no physical board/recovery validation",
            "SPDX inventory is not artifact signing or reproducibility attestation",
        ],
    }
    receipt_path = output / (
        "ANTICIPY_BUILD_RECEIPT.json"
        if candidate_accepted
        else "ANTICIPY_BUILD_FAILURE_RECEIPT.json"
    )
    write_json(receipt_path, receipt)
    if not candidate_accepted:
        raise RuntimeError(
            f"candidate build or provenance check failed; inspect {receipt_path}"
        )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument(
        "--source",
        type=Path,
        default=FIRMWARE_ROOT / ".cache" / "omi-v2.0.1-Omi-firmware-v1.0",
    )
    parser.add_argument(
        "--materialized-source",
        type=Path,
        default=FIRMWARE_ROOT / ".build" / "source" / "anticipy-v2.0.1",
    )
    parser.add_argument(
        "--ncs-workspace",
        type=Path,
        default=FIRMWARE_ROOT / ".build" / "ncs-v2.5.0",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=FIRMWARE_ROOT / ".build" / "candidate" / "anticipy-v2.0.1",
    )
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    ncs_workspace = args.ncs_workspace.expanduser().resolve()
    status = probe(source, ncs_workspace)
    print(json.dumps(status, indent=2, sort_keys=True))
    if args.probe:
        return 0
    try:
        receipt = build(
            source,
            args.materialized_source.expanduser().resolve(),
            ncs_workspace,
            args.output.expanduser(),
            status,
        )
    except RuntimeError as exc:
        print(f"refusing candidate build: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
