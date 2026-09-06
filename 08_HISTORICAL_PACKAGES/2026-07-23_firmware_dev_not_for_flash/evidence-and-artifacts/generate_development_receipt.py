#!/usr/bin/env python3
"""Emit development-only firmware evidence. Never signs, flashes, or approves."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        temporary.unlink()
    temporary.write_bytes(canonical(value))
    os.replace(temporary, path)


def run(*args: str, cwd: Path | None = None) -> str:
    environment = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "/bin/false",
    }
    return subprocess.run(
        args,
        cwd=cwd,
        env=environment,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def git(path: Path, *args: str) -> str:
    return run("git", "-c", "credential.helper=", *args, cwd=path)


def parse_tsv(path: Path) -> list[tuple[str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        left, right = line.split("\t", 1)
        rows.append((left, right))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--image-manifest", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()

    base = args.base.resolve()
    development = base / "development"
    candidate = base / "candidate-checkout"
    workspace = base / "ncs/workspace"
    source = candidate / "firmware/.build/source/anticipy-v2.0.1"
    artifact_root = development / "output/zephyr"
    control = args.control.resolve()
    control_lock_path = control.parent / "control-lock.json"
    source_receipt_path = source / "ANTICIPY_SOURCE_RECEIPT.json"
    source_receipt = json.loads(source_receipt_path.read_text())
    toolchain_lock = json.loads(
        (candidate / "firmware/replacement/toolchain.lock.json").read_text()
    )
    if git(workspace / "nrf", "rev-parse", "HEAD") != toolchain_lock[
        "nrf_connect_sdk"
    ]["commit"]:
        raise RuntimeError("NCS commit drifted")
    if git(workspace / "zephyr", "rev-parse", "HEAD") != toolchain_lock[
        "zephyr"
    ]["commit"]:
        raise RuntimeError("Zephyr commit drifted")
    if sha256(workspace / "nrf/west.yml") != toolchain_lock["nrf_connect_sdk"][
        "west_manifest_sha256"
    ]:
        raise RuntimeError("NCS west manifest drifted")
    if sha256(workspace / ".west/config") != (
        "cf1cf23eeb6d3d45215031bcc9c029ecb805497b6fc20b997f49f995c7895ea6"
    ):
        raise RuntimeError("original west config drifted")
    effective_west_config = base / "development-west-config/config"
    if sha256(effective_west_config) != (
        "59620dc18f46833ec79da979b1869516220c11c4347b80b2d69c0b4c82bb2cce"
    ):
        raise RuntimeError("effective writable west config drifted")
    if effective_west_config.read_text() != (
        (workspace / ".west/config").read_text()
        + "[zephyr]\nbase = zephyr\n\n"
    ):
        raise RuntimeError("effective west config has an unexpected amendment")

    candidate_commit = git(candidate, "rev-parse", "HEAD")
    if candidate_commit != "5786f71b38b7a07ef5cb590159d77c4808059525":
        raise RuntimeError("candidate checkout drifted")
    if git(candidate, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("candidate checkout is dirty")

    pre = development / "ACTIVE_WEST_PROJECTS_PRE.tsv"
    post = development / "ACTIVE_WEST_PROJECTS_POST.tsv"
    if pre.read_bytes() != post.read_bytes():
        raise RuntimeError("active project inventory changed during build")

    projects = []
    for relative, commit in parse_tsv(pre):
        project = (workspace / relative).resolve()
        if workspace not in project.parents:
            raise RuntimeError("active project escapes workspace")
        if git(project, "rev-parse", "HEAD") != commit:
            raise RuntimeError(f"active project drifted: {relative}")
        if git(
            project,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ):
            raise RuntimeError(f"active project is dirty: {relative}")
        remotes = git(project, "remote").splitlines()
        if len(remotes) != 1:
            raise RuntimeError(
                f"active project does not have exactly one remote: {relative}"
            )
        remote_name = remotes[0]
        repository = git(project, "remote", "get-url", remote_name)
        parsed = urlsplit(repository)
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise RuntimeError(f"active project remote is unsafe: {relative}")
        projects.append(
            {
                "commit": commit,
                "path": relative,
                "remote_name": remote_name,
                "repository": repository,
            }
        )

    artifacts = {}
    for name in ("zephyr.elf", "zephyr.hex", "zephyr.bin", "zephyr.uf2", "zephyr.map"):
        path = artifact_root / name
        artifacts[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}

    spec = importlib.util.spec_from_file_location("trusted_control", control)
    trusted_control = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(trusted_control)
    uf2 = trusted_control.inspect_uf2(
        artifact_root / "zephyr.uf2", trusted_control.load_lock()
    )

    cache_entries = {}
    for line in (development / "output/CMakeCache.txt").read_text().splitlines():
        if "=" not in line or ":" not in line.split("=", 1)[0]:
            continue
        left, value = line.split("=", 1)
        key, kind = left.split(":", 1)
        if key in {
            "BOARD",
            "BOARD_DIR",
            "CACHED_BOARD",
            "CACHED_CONF_FILE",
            "CMAKE_HOME_DIRECTORY",
            "DTC_OVERLAY_FILE",
            "ZEPHYR_BASE",
        }:
            if key in cache_entries:
                raise RuntimeError(f"duplicate CMake cache entry: {key}")
            cache_entries[key] = (kind, value)
    expected_cache = {
        "BOARD": ("STRING", "xiao_ble_sense"),
        "CACHED_BOARD": ("STRING", "xiao_ble_sense"),
        "BOARD_DIR": ("PATH", "/ncs/zephyr/boards/arm/xiao_ble"),
        "CACHED_CONF_FILE": (
            "STRING",
            "prj_xiao_ble_sense_devkitv2-adafruit.conf",
        ),
        "CMAKE_HOME_DIRECTORY": (
            "INTERNAL",
            "/candidate/firmware/.build/source/anticipy-v2.0.1",
        ),
        "DTC_OVERLAY_FILE": (
            "STRING",
            "overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay",
        ),
        "ZEPHYR_BASE": ("PATH", "/ncs/zephyr"),
    }
    if cache_entries != expected_cache:
        raise RuntimeError("locked CMake cache entries drifted")
    resolved_cache_paths = {
        "BOARD_DIR": "/ncs/zephyr/boards/arm/xiao_ble",
        "CACHED_CONF_FILE": (
            "/candidate/firmware/.build/source/anticipy-v2.0.1/"
            "prj_xiao_ble_sense_devkitv2-adafruit.conf"
        ),
        "CMAKE_HOME_DIRECTORY": (
            "/candidate/firmware/.build/source/anticipy-v2.0.1"
        ),
        "DTC_OVERLAY_FILE": (
            "/candidate/firmware/.build/source/anticipy-v2.0.1/"
            "overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay"
        ),
        "ZEPHYR_BASE": "/ncs/zephyr",
    }
    if not (
        (workspace / "zephyr/boards/arm/xiao_ble").is_dir()
        and (source / "prj_xiao_ble_sense_devkitv2-adafruit.conf").is_file()
        and (
            source
            / "overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay"
        ).is_file()
    ):
        raise RuntimeError("resolved CMake inputs are absent from locked mounts")

    dotconfig = (development / "output/zephyr/.config").read_text()
    required_config = {
        'CONFIG_BT_DEVICE_NAME="Anticipy"',
        'CONFIG_BT_DIS_MODEL="Anticipy Pendant"',
        "CONFIG_BT_BAS=y",
        "CONFIG_BT_PERIPHERAL=y",
        "CONFIG_FLASH_LOAD_OFFSET=0x27000",
    }
    if not required_config.issubset(set(dotconfig.splitlines())):
        raise RuntimeError("compiled Kconfig contract markers are missing")
    binary_strings = set(
        run("strings", str(artifact_root / "zephyr.elf")).splitlines()
    )
    if not {"Anticipy", "Anticipy Pendant"}.issubset(binary_strings):
        raise RuntimeError("compiled product markers are missing")

    image_manifest = json.loads(args.image_manifest.read_text())
    layer_bytes = sum(int(item["size"]) for item in image_manifest["layers"])
    expected_image = toolchain_lock["toolchain_container"]
    if image_manifest["config"]["digest"] != (
        "sha256:207d3b4bb50b2e6b4252c53d654c315f8960af1a2f7bcd5b26ed1b44c7f9fc29"
    ):
        raise RuntimeError("image config digest drifted")

    inspection = json.loads(run("docker", "inspect", args.container))[0]
    host = inspection["HostConfig"]
    state = inspection["State"]
    mounts = {item["Destination"]: item for item in inspection["Mounts"]}
    if (
        mounts["/ncs"]["RW"]
        or Path(mounts["/ncs"]["Source"]).resolve() != workspace
        or not mounts["/ncs/.west/config"]["RW"]
        or Path(mounts["/ncs/.west/config"]["Source"]).resolve()
        != effective_west_config.resolve()
    ):
        raise RuntimeError("west configuration mount evidence drifted")
    expected_tmpfs = {
        "/home/ci": "rw,nosuid,nodev,size=128m,mode=0700",
        "/tmp": "rw,nosuid,nodev,noexec,size=1g",
        "/usr/local/share/nrfutil/logs": (
            "rw,nosuid,nodev,noexec,size=16m,mode=0755"
        ),
    }
    if (
        inspection["Image"] != expected_image["digest"]
        or state["ExitCode"] != 0
        or state["OOMKilled"]
        or host["NetworkMode"] != "none"
        or not host["ReadonlyRootfs"]
        or host["Privileged"]
        or host["CapDrop"] != ["ALL"]
        or "no-new-privileges" not in host["SecurityOpt"]
        or host["Devices"]
        or host["Tmpfs"] != expected_tmpfs
    ):
        raise RuntimeError("development container hardening drifted")
    container_evidence = {
        "schema": 1,
        "status": "LOCAL_DEVELOPMENT_CONTAINER_INSPECTION_NOT_ATTESTED",
        "name": args.container,
        "image": inspection["Config"]["Image"],
        "image_id": inspection["Image"],
        "command": inspection["Config"]["Cmd"],
        "entrypoint": inspection["Config"]["Entrypoint"],
        "working_directory": inspection["Config"]["WorkingDir"],
        "state": {
            key: state[key]
            for key in (
                "Status",
                "ExitCode",
                "OOMKilled",
                "StartedAt",
                "FinishedAt",
            )
        },
        "host_configuration": {
            "network_mode": host["NetworkMode"],
            "read_only_root": host["ReadonlyRootfs"],
            "privileged": host["Privileged"],
            "cap_drop": host["CapDrop"],
            "security_opt": host["SecurityOpt"],
            "devices": host["Devices"],
            "tmpfs": host["Tmpfs"],
            "memory_bytes": host["Memory"],
            "memory_swap_bytes": host["MemorySwap"],
            "nano_cpus": host["NanoCpus"],
            "pids_limit": host["PidsLimit"],
        },
        "mounts": [
            {
                "source": item["Source"],
                "destination": item["Destination"],
                "read_write": item["RW"],
                "type": item["Type"],
            }
            for item in sorted(
                inspection["Mounts"], key=lambda value: value["Destination"]
            )
        ],
        "is_independent_attestation": False,
        "is_production_replica": False,
    }
    container_evidence_path = (
        development
        / "ANTICIPY_DEVELOPMENT_CONTAINER_INSPECTION_NOT_ATTESTED.json"
    )
    write_json(container_evidence_path, container_evidence)

    components = {
        "schema": 1,
        "status": "DEVELOPMENT_COMPONENT_INVENTORY_NOT_AN_SPDX_SBOM_NOT_ATTESTED",
        "candidate_commit": candidate_commit,
        "source": {
            "content_tree_sha256": source_receipt["materialized_source"][
                "content_tree_sha256"
            ],
            "patch_sha256": source_receipt["patch"]["sha256"],
            "source_receipt_sha256": sha256(source_receipt_path),
            "upstream_commit": source_receipt["upstream"]["commit"],
            "upstream_repository": source_receipt["upstream"]["repository"],
        },
        "active_west_projects": projects,
        "toolchain_container": {
            "config_digest": image_manifest["config"]["digest"],
            "digest": expected_image["digest"],
            "image": expected_image["image"],
            "manifest_compressed_layer_bytes": layer_bytes,
            "manifest_sha256": sha256(args.image_manifest),
            "platform": expected_image["platform"],
        },
        "artifacts": artifacts,
        "flash_approved": False,
        "flash_performed": False,
    }
    components_path = (
        development
        / "ANTICIPY_DEVELOPMENT_COMPONENT_INVENTORY_NOT_ATTESTED.json"
    )
    write_json(components_path, components)

    tool_versions = dict(parse_tsv(development / "TOOL_VERSIONS.tsv"))
    receipt = {
        "schema": 1,
        "status": "QUARANTINED_DEVELOPMENT_BUILD_SUCCEEDED_NOT_FOR_FLASH",
        "classification": (
            "single local development build; not a release, signature, "
            "two-replica attestation, flash authorization, or hardware proof"
        ),
        "receipt_generator_sha256": sha256(Path(__file__).resolve()),
        "candidate": {
            "commit": candidate_commit,
            "source_receipt_sha256": sha256(source_receipt_path),
            "content_tree_sha256": source_receipt["materialized_source"][
                "content_tree_sha256"
            ],
            "patch_sha256": source_receipt["patch"]["sha256"],
            "upstream_commit": source_receipt["upstream"]["commit"],
            "upstream_source_tree_git_oid": source_receipt["upstream"][
                "source_tree_git_oid"
            ],
        },
        "ncs": {
            "nrf_commit": toolchain_lock["nrf_connect_sdk"]["commit"],
            "zephyr_commit": toolchain_lock["zephyr"]["commit"],
            "west_manifest_sha256": toolchain_lock["nrf_connect_sdk"][
                "west_manifest_sha256"
            ],
            "west_configuration": {
                "canonical_host_config": {
                    "observed_post_build_sha256": (
                        "cf1cf23eeb6d3d45215031bcc9c029ecb805497b6fc20b997f49f995c7895ea6"
                    ),
                    "mounted_read_only_as_part_of_ncs_workspace": True,
                    "changed_by_build": False,
                },
                "effective_writable_overlay": {
                    "initial_sha256_required_by_executed_build_guard": (
                        "cf1cf23eeb6d3d45215031bcc9c029ecb805497b6fc20b997f49f995c7895ea6"
                    ),
                    "observed_post_build_sha256": (
                        "59620dc18f46833ec79da979b1869516220c11c4347b80b2d69c0b4c82bb2cce"
                    ),
                    "west_appended": ["[zephyr]", "base = zephyr"],
                    "mounted_at": "/ncs/.west/config",
                    "changed_by_build": True,
                },
            },
            "active_project_count": len(projects),
            "active_project_inventory_sha256": sha256(pre),
            "active_inventory_identical_pre_post": True,
            "all_manifest_project_count": 64,
            "inactive_uncloned_project_count": 19,
            "full_manifest_freeze_available": False,
            "full_manifest_freeze_blockers": [
                "nrf-802154 repository requested authentication",
                "dragoon points to an unavailable Nordic-internal Bitbucket host",
                "west 1.1 refuses freeze until every inactive/private project is cloned",
            ],
        },
        "toolchain": {
            "image": expected_image["image"],
            "image_digest": expected_image["digest"],
            "image_config_digest": image_manifest["config"]["digest"],
            "image_manifest_sha256": sha256(args.image_manifest),
            "image_manifest_compressed_layer_bytes": layer_bytes,
            "platform": expected_image["platform"],
            "versions": tool_versions,
            "container": {
                "started_at": state["StartedAt"],
                "finished_at": state["FinishedAt"],
                "exit_code": state["ExitCode"],
                "oom_killed": state["OOMKilled"],
                "network_mode": host["NetworkMode"],
                "read_only_root": host["ReadonlyRootfs"],
                "privileged": host["Privileged"],
                "cap_drop": host["CapDrop"],
                "security_opt": host["SecurityOpt"],
                "host_devices": host["Devices"],
            },
            "container_inspection": {
                "filename": container_evidence_path.name,
                "sha256": sha256(container_evidence_path),
                "is_independent_attestation": False,
            },
            "execution_identity": (
                "locally observed Docker digest and config; not independent OCI/CI attestation"
            ),
        },
        "build": {
            "command": (development / "BUILD_COMMAND.txt").read_text().strip(),
            "command_sha256": sha256(development / "BUILD_COMMAND.txt"),
            "exit_code": int(
                (development / "BUILD_EXIT_CODE.txt").read_text().strip()
            ),
            "log_sha256": sha256(development / "BUILD.log"),
            "cmake_cache_sha256": sha256(development / "output/CMakeCache.txt"),
            "cmake_inputs_verified": True,
            "cmake_cache_locked_entries": {
                key: {"type": kind, "value": value}
                for key, (kind, value) in sorted(cache_entries.items())
            },
            "cmake_resolved_container_paths": resolved_cache_paths,
            "board": "xiao_ble_sense",
            "board_definition_git_tree_oid": (
                "8703fc4ab1f5bb7dca23c679ba2c681b34067c22"
            ),
            "configuration_file": (
                "prj_xiao_ble_sense_devkitv2-adafruit.conf"
            ),
            "devicetree_overlay": (
                "overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay"
            ),
            "source_date_epoch": 1728134730,
            "flash_used_bytes": 274468,
            "ram_used_bytes": 210160,
            "artifacts": artifacts,
            "trusted_control_uf2_validation": uf2,
            "elf": {
                "class": "ELF32",
                "endianness": "little",
                "machine": "ARM",
                "type": "EXEC",
                "validated_symbols": [
                    "audio_codec_read_characteristic",
                    "battery_smoother_reset",
                    "battery_smoother_update",
                    "broadcast_battery_level",
                    "transport_start",
                ],
            },
            "compiled_contract_markers": [
                "Anticipy",
                "Anticipy Pendant",
                "CONFIG_BT_BAS=y",
                "CONFIG_BT_DEVICE_NAME=\"Anticipy\"",
                "CONFIG_BT_DIS_MODEL=\"Anticipy Pendant\"",
                "CONFIG_FLASH_LOAD_OFFSET=0x27000",
            ],
        },
        "component_inventory": {
            "filename": components_path.name,
            "sha256": sha256(components_path),
            "is_spdx_release_sbom": False,
            "is_attestation": False,
        },
        "control_contract_failures": [
            "original read-only container blocks nrfutil logger and toolchains.json lock",
            "original HOME=/home/ci plus host UID cannot reach the image toolchain under /root",
            "original image workdir is already a different baked west workspace",
            "original west init --mr raw SHA maps to unsupported git clone --branch SHA",
            "original active-only west update cannot satisfy west manifest --freeze",
            "inactive manifest includes inaccessible/private repositories",
            "exact runtime constructor fails because pinned environment lacks zlib.h",
        ],
        "release_sbom_emitted": False,
        "production_candidate_gate_passed": False,
        "two_replica_attested": False,
        "flash_approved": False,
        "flash_performed": False,
        "physical_hardware_verified": False,
        "physical_ble_verified": False,
        "physical_battery_verified": False,
        "haptic_verified": False,
        "secure_update_added": False,
    }
    receipt_path = (
        development / "ANTICIPY_DEVELOPMENT_BUILD_RECEIPT_NOT_FOR_FLASH.json"
    )
    write_json(receipt_path, receipt)

    package = args.package.expanduser().resolve()
    if package.exists():
        raise RuntimeError("package destination already exists")
    package.mkdir(parents=True)
    payload = package / "evidence-and-artifacts"
    payload.mkdir()
    sources = [
        receipt_path,
        components_path,
        container_evidence_path,
        source_receipt_path,
        args.image_manifest.resolve(),
        Path(__file__).resolve(),
        pre,
        post,
        development / "ARTIFACT_SHA256SUMS.txt",
        development / "BUILD.log",
        development / "BUILD_COMMAND.txt",
        development / "DEVELOPMENT_STATUS_NOT_FOR_FLASH.txt",
        development / "TOOL_VERSIONS.tsv",
        development / "output/CMakeCache.txt",
        development / "output/zephyr/.config",
        development / "output/zephyr/zephyr.dts",
        *(artifact_root / name for name in artifacts),
    ]
    for source_path in sources:
        target = payload / source_path.name
        if target.exists():
            raise RuntimeError(f"duplicate package filename: {target.name}")
        shutil.copy2(source_path, target)
    warning = (
        "ANTICIPY DEVELOPMENT FIRMWARE — NOT FOR FLASH\n\n"
        "This package proves one offline development build only.\n"
        "It is not signed, release-approved, two-replica-attested, recovery-tested,\n"
        "or physically verified. Do not copy zephyr.uf2 to a pendant.\n"
        "Read ANTICIPY_DEVELOPMENT_BUILD_RECEIPT_NOT_FOR_FLASH.json for exact evidence.\n"
    )
    (package / "00_READ_ME_FIRST_NOT_FOR_FLASH.txt").write_text(warning)
    hashes = []
    for path in sorted(package.rglob("*")):
        if path.is_file():
            hashes.append(
                f"{sha256(path)}  {path.relative_to(package).as_posix()}"
            )
    (package / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
