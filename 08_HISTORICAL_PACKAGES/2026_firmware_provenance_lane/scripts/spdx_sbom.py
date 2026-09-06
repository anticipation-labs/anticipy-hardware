#!/usr/bin/env python3
"""Create the deterministic SPDX 2.3 SBOM for a verified firmware build.

The builder supplies only already-locked provenance plus artifact records.  Local
paths, wall-clock time, usernames, environment values, and tool output never enter
the document.  This module does not build, sign, inspect, or flash hardware.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


SPDX_FILENAME = "ANTICIPY_FIRMWARE_SBOM.spdx.json"
SPDX_VERSION = "SPDX-2.3"
SPDX_DATA_LICENSE = "CC0-1.0"
SPDX_DOCUMENT_ID = "SPDXRef-DOCUMENT"
SPDX_MAIN_PACKAGE_ID = "SPDXRef-Package-Anticipy-Pendant-Firmware-Candidate"
SPDX_SOURCE_PACKAGE_ID = "SPDXRef-Package-Anticipy-Source"
SPDX_TOOLCHAIN_PACKAGE_ID = "SPDXRef-Package-Nordic-Toolchain-Container"
ACTIVE_PROJECTS_FILENAME = "west-active-projects-frozen.tsv"
FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
SPDX_SCHEMA_PATH = FIRMWARE_ROOT / "replacement" / "spdx-2.3.schema.json.b64"
SPDX_SCHEMA_LOCK_PATH = FIRMWARE_ROOT / "replacement" / "spdx-schema.lock.json"
SPDX_SCHEMA_LICENSE_PATH = (
    FIRMWARE_ROOT / "LICENSES" / "SPDX-spdx-spec-CC-BY-3.0.txt"
)
SPDX_SCHEMA_REVISION = "aadf3b0b8dbbabdb4d880b0fc714255fea436ff7"
SPDX_SCHEMA_SHA256 = "239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b"
SPDX_SCHEMA_LICENSE_SHA256 = (
    "a69d068ec0e987513259d3d355f10c1b39cae1bfb275e8a6ed250b8c1d17531f"
)
SPDX_SCHEMA_UPSTREAM_LICENSE_SHA256 = (
    "017e38491cccbd2bdb6da0a32a33db9ec245b5dab30fdcd09f2c742c975e5b35"
)
SBOM_GENERATOR_NAME = "anticipy-firmware-spdx"
SBOM_GENERATOR_VERSION = "1.0.0"
SBOM_PYTHON_IMPLEMENTATION = "CPython"
SBOM_PYTHON_VERSION = "3.10.14"
SBOM_JSONSCHEMA_VERSION = "4.26.0"
SBOM_PYYAML_VERSION = "6.0.3"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SPDX_ID = re.compile(r"^SPDXRef-[A-Za-z0-9.-]+$")
_ARTIFACT_NAMES = {
    "zephyr.elf": "APPLICATION",
    "zephyr.hex": "BINARY",
    "zephyr.bin": "BINARY",
    "zephyr.uf2": "BINARY",
    "zephyr.map": "TEXT",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def spdx_json_bytes(document: dict) -> bytes:
    """Return the one canonical on-disk representation used by the builder."""

    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _require_dict(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be an object")
    return value


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or any(
        ord(character) < 0x20 for character in value
    ):
        raise RuntimeError(f"{label} must be a non-empty printable string")
    return value


def _require_sha256(value: object, label: str) -> str:
    value = _require_string(value, label)
    if not _SHA256.fullmatch(value):
        raise RuntimeError(f"{label} must be a lowercase SHA-256")
    return value


def _require_git_commit(value: object, label: str) -> str:
    value = _require_string(value, label)
    if not _GIT_COMMIT.fullmatch(value):
        raise RuntimeError(f"{label} must be a 40-character Git commit")
    return value


def _https_url(value: object, label: str) -> str:
    value = _require_string(value, label)
    parsed = urlsplit(value)
    if (
        any(character.isspace() for character in value)
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(f"{label} must be credential-free canonical HTTPS")
    return value


def _source_date_timestamp(value: object) -> tuple[int, str]:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("SOURCE_DATE_EPOCH must be a non-negative integer")
    try:
        created = datetime.fromtimestamp(value, timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except (OverflowError, OSError, ValueError) as exc:
        raise RuntimeError("SOURCE_DATE_EPOCH is outside the supported range") from exc
    return value, created


def reject_symlink_ancestors(path: Path, label: str) -> Path:
    """Return an absolute path after rejecting symlinks at every existing level."""

    path = Path(path)
    if any(part == os.pardir for part in path.parts):
        raise RuntimeError(f"{label} must not contain parent traversal")
    absolute = path if path.is_absolute() else Path.cwd() / path
    candidate = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        candidate /= part
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise RuntimeError(f"cannot inspect {label} path safely") from exc
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"{label} must not traverse a symlink")
    return absolute


def _regular_file_without_symlinks(path: Path, label: str) -> Path:
    absolute = reject_symlink_ancestors(path, label)
    if not absolute.is_file():
        raise RuntimeError(f"{label} is missing or not a regular file")
    return absolute


def _project_path(value: object) -> str:
    value = _require_string(value, "west project path")
    if "\\" in value or any(character.isspace() for character in value):
        raise RuntimeError("west project path must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or value in {".", ".."} or any(
        part in {"", ".", ".."} for part in path.parts
    ) or path.as_posix() != value or path.parts[0] == ".west":
        raise RuntimeError("west project path must be relative and normalized")
    return path.as_posix()


def _validate_source(
    replacement: dict,
    source_receipt: dict,
    source_receipt_sha256: str,
    toolchain_lock_sha256: str,
) -> dict:
    replacement = _require_dict(replacement, "replacement lock")
    source_receipt = _require_dict(source_receipt, "source receipt")
    source_receipt_sha256 = _require_sha256(
        source_receipt_sha256, "source receipt SHA-256"
    )
    toolchain_lock_sha256 = _require_sha256(
        toolchain_lock_sha256, "toolchain lock SHA-256"
    )

    materialized = _require_dict(
        replacement.get("materialized_source"), "replacement materialized source"
    )
    if source_receipt_sha256 != _require_sha256(
        materialized.get("source_receipt_sha256"),
        "locked source receipt SHA-256",
    ):
        raise RuntimeError("source receipt SHA-256 does not match replacement lock")
    if source_receipt.get("upstream") != replacement.get("upstream"):
        raise RuntimeError("source receipt upstream provenance drifted")
    if source_receipt.get("patch") != replacement.get("patch"):
        raise RuntimeError("source receipt patch provenance drifted")
    receipt_materialized = _require_dict(
        source_receipt.get("materialized_source"),
        "source receipt materialized source",
    )
    content_tree_sha256 = _require_sha256(
        receipt_materialized.get("content_tree_sha256"),
        "materialized content-tree SHA-256",
    )
    if content_tree_sha256 != _require_sha256(
        materialized.get("content_tree_sha256"),
        "locked materialized content-tree SHA-256",
    ):
        raise RuntimeError("materialized source content-tree SHA-256 drifted")
    if source_receipt.get("toolchain_lock_sha256") != toolchain_lock_sha256:
        raise RuntimeError("source receipt toolchain lock SHA-256 drifted")
    if source_receipt.get("artifact_built") is not False:
        raise RuntimeError("source receipt must not claim a built artifact")
    if source_receipt.get("flash_performed") is not False:
        raise RuntimeError("source receipt must not claim a flash")

    upstream = _require_dict(replacement.get("upstream"), "replacement upstream")
    patch = _require_dict(replacement.get("patch"), "replacement patch")
    repository = _https_url(upstream.get("repository"), "upstream repository")
    return {
        "repository": repository,
        "commit": _require_git_commit(upstream.get("commit"), "upstream commit"),
        "patch_sha256": _require_sha256(patch.get("sha256"), "patch SHA-256"),
        "content_tree_sha256": content_tree_sha256,
        "source_receipt_sha256": source_receipt_sha256,
        "toolchain_lock_sha256": toolchain_lock_sha256,
    }


def _validate_ncs(
    toolchain: dict,
    pre_ncs: dict,
    post_ncs: dict,
    active_projects_path: Path,
) -> tuple[dict[str, str], dict, dict[str, str | None]]:
    toolchain = _require_dict(toolchain, "toolchain lock")
    pre_ncs = _require_dict(pre_ncs, "pre-build NCS provenance")
    post_ncs = _require_dict(post_ncs, "post-build NCS provenance")
    active_projects, active_projects_sha256 = _validate_active_projects_snapshot(
        active_projects_path
    )
    expected_ncs = _require_dict(
        toolchain.get("nrf_connect_sdk"), "NCS toolchain lock"
    )
    expected_zephyr = _require_dict(toolchain.get("zephyr"), "Zephyr toolchain lock")

    def validated_snapshot(
        snapshot: dict, label: str
    ) -> tuple[dict[str, str], dict[str, str]]:
        projects = _require_dict(snapshot.get("project_commits"), f"{label} projects")
        normalized: dict[str, str] = {}
        for raw_path, raw_commit in projects.items():
            path = _project_path(raw_path)
            if path in normalized:
                raise RuntimeError(f"{label} contains a duplicate west project")
            normalized[path] = _require_git_commit(
                raw_commit, f"{label} west project commit"
            )
        normalized = dict(sorted(normalized.items()))
        count = snapshot.get("project_count")
        if isinstance(count, bool) or not isinstance(count, int) or count != len(normalized):
            raise RuntimeError(f"{label} west project count is inconsistent")
        expected_commits_hash = canonical_json_sha256(normalized)
        if snapshot.get("project_commits_sha256") != expected_commits_hash:
            raise RuntimeError(f"{label} west project commit-set SHA-256 drifted")
        if snapshot.get("ncs_commit") != normalized.get("nrf"):
            raise RuntimeError(f"{label} NCS commit is inconsistent")
        if snapshot.get("zephyr_commit") != normalized.get("zephyr"):
            raise RuntimeError(f"{label} Zephyr commit is inconsistent")
        if snapshot.get("west_manifest_sha256") != expected_ncs.get(
            "west_manifest_sha256"
        ):
            raise RuntimeError(f"{label} NCS west.yml SHA-256 drifted")
        _require_sha256(
            snapshot.get("west_config_sha256"),
            f"{label} .west/config SHA-256",
        )
        if snapshot.get("active_projects_frozen_filename") != ACTIVE_PROJECTS_FILENAME:
            raise RuntimeError(f"{label} active west project filename drifted")
        if snapshot.get("active_projects_frozen_sha256") != active_projects_sha256:
            raise RuntimeError(f"{label} active west project snapshot SHA-256 drifted")
        active_count = snapshot.get("active_projects_frozen_project_count")
        if (
            isinstance(active_count, bool)
            or not isinstance(active_count, int)
            or active_count != len(active_projects)
        ):
            raise RuntimeError(
                f"{label} active west project snapshot count is inconsistent"
            )

        raw_repositories = _require_dict(
            snapshot.get("project_repositories"),
            f"{label} west project repositories",
        )
        repositories: dict[str, str] = {}
        for raw_path, raw_repository in raw_repositories.items():
            path = _project_path(raw_path)
            if path in repositories:
                raise RuntimeError(
                    f"{label} contains a duplicate west project repository"
                )
            repositories[path] = _https_url(
                raw_repository, f"{label} west project repository"
            )
        repositories = dict(sorted(repositories.items()))
        if set(repositories) != set(normalized):
            raise RuntimeError(
                f"{label} west project repository set does not match projects"
            )
        if snapshot.get("project_repositories_sha256") != canonical_json_sha256(
            repositories
        ):
            raise RuntimeError(
                f"{label} west project repository-set SHA-256 drifted"
            )
        return normalized, repositories

    pre_projects, pre_repositories = validated_snapshot(pre_ncs, "pre-build")
    post_projects, post_repositories = validated_snapshot(post_ncs, "post-build")
    if pre_projects != post_projects or pre_projects != active_projects:
        raise RuntimeError("active west project commits changed during the build")
    if pre_repositories != post_repositories:
        raise RuntimeError("active west project repositories changed during the build")
    if pre_ncs.get("west_config_sha256") != post_ncs.get("west_config_sha256"):
        raise RuntimeError(".west/config changed during the build")
    if pre_ncs.get("west_manifest_sha256") != post_ncs.get("west_manifest_sha256"):
        raise RuntimeError("nrf/west.yml changed during the build")
    if pre_projects.get("nrf") != _require_git_commit(
        expected_ncs.get("commit"), "locked NCS commit"
    ):
        raise RuntimeError("NCS commit does not match toolchain lock")
    if pre_projects.get("zephyr") != _require_git_commit(
        expected_zephyr.get("commit"), "locked Zephyr commit"
    ):
        raise RuntimeError("Zephyr commit does not match toolchain lock")
    ncs_repository = _https_url(
        expected_ncs.get("repository"), "locked NCS repository"
    )
    zephyr_repository = _https_url(
        expected_zephyr.get("repository"), "locked Zephyr repository"
    )
    if pre_repositories.get("nrf") != ncs_repository:
        raise RuntimeError("active NCS repository does not match toolchain lock")
    observed_zephyr_repository = pre_repositories.get("zephyr")
    if observed_zephyr_repository is None or (
        observed_zephyr_repository.rstrip("/").removesuffix(".git")
        != zephyr_repository.rstrip("/").removesuffix(".git")
    ):
        raise RuntimeError("active Zephyr repository does not match toolchain lock")
    project_locations = dict(pre_repositories)
    project_locations["nrf"] = ncs_repository
    project_locations["zephyr"] = zephyr_repository
    return pre_projects, {
        "active_projects_frozen_filename": ACTIVE_PROJECTS_FILENAME,
        "active_projects_frozen_sha256": active_projects_sha256,
        "active_projects_frozen_project_count": len(active_projects),
        "nrf_west_yml_sha256": _require_sha256(
            expected_ncs.get("west_manifest_sha256"),
            "locked NCS west.yml SHA-256",
        ),
        "west_config_sha256": _require_sha256(
            pre_ncs.get("west_config_sha256"),
            "pre-build .west/config SHA-256",
        ),
    }, project_locations


def _validate_active_projects_snapshot(
    path: Path,
) -> tuple[dict[str, str], str]:
    path = _regular_file_without_symlinks(
        path, "active west project snapshot"
    )
    content = path.read_bytes()
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("active west project snapshot is not UTF-8") from exc
    if not text or not text.endswith("\n") or "\r" in text:
        raise RuntimeError("active west project snapshot is not canonical TSV")

    projects: dict[str, str] = {}
    observed_paths: list[str] = []
    for line in text.splitlines():
        fields = line.split("\t")
        if len(fields) != 2:
            raise RuntimeError("active west project snapshot row is malformed")
        path_value = _project_path(fields[0])
        if path_value in projects:
            raise RuntimeError(
                "active west project snapshot contains a duplicate project path"
            )
        projects[path_value] = _require_git_commit(
            fields[1], "active west project snapshot HEAD"
        )
        observed_paths.append(path_value)
    if observed_paths != sorted(observed_paths):
        raise RuntimeError("active west project snapshot is not sorted")
    if "nrf" not in projects:
        raise RuntimeError("active west project snapshot does not include nrf")
    canonical = "".join(
        f"{project_path}\t{projects[project_path]}\n"
        for project_path in sorted(projects)
    ).encode("utf-8")
    if content != canonical:
        raise RuntimeError("active west project snapshot bytes are not canonical")
    return dict(sorted(projects.items())), hashlib.sha256(content).hexdigest()


def _validate_container(toolchain: dict, declaration_matched: object) -> dict:
    if declaration_matched is not True:
        raise RuntimeError("toolchain container digest declaration did not match")
    container = _require_dict(
        toolchain.get("toolchain_container"), "toolchain container lock"
    )
    image = _require_string(container.get("image"), "toolchain container image")
    if (
        any(character.isspace() for character in image)
        or "://" in image
        or "@" in image
        or image.startswith("/")
        or ".." in PurePosixPath(image).parts
    ):
        raise RuntimeError("toolchain container image is malformed")
    digest = _require_string(container.get("digest"), "toolchain container digest")
    if not digest.startswith("sha256:"):
        raise RuntimeError("toolchain container digest must use SHA-256")
    digest_sha256 = _require_sha256(digest.removeprefix("sha256:"), "container digest")
    return {
        "image": image,
        "digest": f"sha256:{digest_sha256}",
        "digest_sha256": digest_sha256,
        "platform": _require_string(
            container.get("platform"), "toolchain container platform"
        ),
        "provenance": "UNVERIFIED_OPERATOR_DECLARATION",
    }


def _validate_artifacts(artifact_root: Path, artifacts: dict) -> dict[str, dict]:
    artifacts = _require_dict(artifacts, "firmware artifacts")
    if "zephyr.uf2" not in artifacts:
        raise RuntimeError("successful candidate SBOM requires zephyr.uf2")
    unexpected = set(artifacts) - set(_ARTIFACT_NAMES)
    if unexpected:
        raise RuntimeError("firmware artifact set contains an unsupported name")

    artifact_root = reject_symlink_ancestors(
        artifact_root, "firmware artifact root"
    )
    if not artifact_root.is_dir():
        raise RuntimeError("firmware artifact root is missing or not a directory")
    zephyr_root = reject_symlink_ancestors(
        artifact_root / "zephyr", "firmware artifact root"
    )
    if not zephyr_root.is_dir():
        raise RuntimeError("firmware artifact root has no zephyr directory")
    actual_known = {
        name
        for name in _ARTIFACT_NAMES
        if (zephyr_root / name).is_file()
    }
    if actual_known != set(artifacts):
        raise RuntimeError("firmware artifact inventory is incomplete or stale")

    validated: dict[str, dict] = {}
    for name in sorted(artifacts):
        record = _require_dict(artifacts[name], f"artifact record {name}")
        size = record.get("bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise RuntimeError(f"artifact size is invalid: {name}")
        expected_sha256 = _require_sha256(
            record.get("sha256"), f"artifact SHA-256 {name}"
        )
        path = _regular_file_without_symlinks(
            zephyr_root / name, f"firmware artifact {name}"
        )
        if path.stat().st_size != size or sha256_file(path) != expected_sha256:
            raise RuntimeError(f"artifact bytes drifted after hashing: {name}")
        validated[name] = {
            "bytes": size,
            "sha256": expected_sha256,
            "file_type": _ARTIFACT_NAMES[name],
        }
    return validated


def validate_artifact_inventory(
    artifact_root: Path, artifacts: dict
) -> dict[str, dict]:
    """Rehash and validate the complete known firmware artifact inventory."""

    return _validate_artifacts(artifact_root, artifacts)


def _spdx_checksum(value: str) -> list[dict[str, str]]:
    return [{"algorithm": "SHA256", "checksumValue": value}]


def _package(
    *,
    spdx_id: str,
    name: str,
    version: str,
    download_location: str,
    comment: str,
    purpose: str,
    checksums: list[dict[str, str]] | None = None,
    external_refs: list[dict[str, str]] | None = None,
) -> dict:
    package = {
        "SPDXID": spdx_id,
        "name": name,
        "versionInfo": version,
        "downloadLocation": download_location,
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
        "comment": comment,
        "primaryPackagePurpose": purpose,
    }
    if checksums:
        package["checksums"] = checksums
    if external_refs:
        package["externalRefs"] = external_refs
    return package


def validate_spdx_document(document: dict) -> None:
    """Validate the required SPDX 2.3 document and reference invariants we emit."""

    if document.get("spdxVersion") != SPDX_VERSION:
        raise RuntimeError("SBOM SPDX version is invalid")
    if document.get("dataLicense") != SPDX_DATA_LICENSE:
        raise RuntimeError("SBOM data license is invalid")
    if document.get("SPDXID") != SPDX_DOCUMENT_ID:
        raise RuntimeError("SBOM document SPDXID is invalid")
    namespace = document.get("documentNamespace")
    if not isinstance(namespace, str) or not namespace.startswith(
        "https://spdx.org/spdxdocs/anticipy-pendant-firmware-"
    ):
        raise RuntimeError("SBOM document namespace is invalid")
    body = dict(document)
    body.pop("documentNamespace", None)
    expected_namespace = (
        "https://spdx.org/spdxdocs/anticipy-pendant-firmware-"
        + canonical_json_sha256(body)
    )
    if namespace != expected_namespace:
        raise RuntimeError("SBOM document namespace does not bind its canonical body")
    creation = _require_dict(document.get("creationInfo"), "SBOM creation info")
    created = creation.get("created")
    if not isinstance(created, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", created
    ):
        raise RuntimeError("SBOM creation timestamp is invalid")
    creators = creation.get("creators")
    expected_creators = [
        f"Tool: {SBOM_GENERATOR_NAME}-{SBOM_GENERATOR_VERSION}",
        f"Tool: CPython-{SBOM_PYTHON_VERSION}",
        f"Tool: jsonschema-{SBOM_JSONSCHEMA_VERSION}",
        f"Tool: PyYAML-{SBOM_PYYAML_VERSION}",
    ]
    if creators != expected_creators:
        raise RuntimeError("SBOM creator does not match pinned generator identity")

    elements = [*document.get("packages", []), *document.get("files", [])]
    ids = {SPDX_DOCUMENT_ID}
    for element in elements:
        spdx_id = element.get("SPDXID")
        if not isinstance(spdx_id, str) or not _SPDX_ID.fullmatch(spdx_id):
            raise RuntimeError("SBOM contains an invalid SPDXID")
        if spdx_id in ids:
            raise RuntimeError("SBOM contains a duplicate SPDXID")
        ids.add(spdx_id)
    if SPDX_MAIN_PACKAGE_ID not in ids:
        raise RuntimeError("SBOM main firmware package is missing")
    if document.get("documentDescribes") != [SPDX_MAIN_PACKAGE_ID]:
        raise RuntimeError("SBOM document description target is invalid")
    for relationship in document.get("relationships", []):
        if relationship.get("spdxElementId") not in ids:
            raise RuntimeError("SBOM relationship source is missing")
        if relationship.get("relatedSpdxElement") not in ids:
            raise RuntimeError("SBOM relationship target is missing")
        _require_string(relationship.get("relationshipType"), "relationship type")
    validate_official_spdx_schema(document)


def _pinned_sbom_identity() -> dict:
    return {
        "generator": {
            "name": SBOM_GENERATOR_NAME,
            "version": SBOM_GENERATOR_VERSION,
        },
        "schema": {
            "format": SPDX_VERSION,
            "revision": SPDX_SCHEMA_REVISION,
            "sha256": SPDX_SCHEMA_SHA256,
            "license_sha256": SPDX_SCHEMA_LICENSE_SHA256,
        },
        "validator": {
            "python_implementation": SBOM_PYTHON_IMPLEMENTATION,
            "python_version": SBOM_PYTHON_VERSION,
            "jsonschema_version": SBOM_JSONSCHEMA_VERSION,
            "pyyaml_version": SBOM_PYYAML_VERSION,
        },
    }


def _load_pinned_schema() -> tuple[dict, dict]:
    schema_path = _regular_file_without_symlinks(
        SPDX_SCHEMA_PATH, "vendored SPDX JSON Schema"
    )
    lock_path = _regular_file_without_symlinks(
        SPDX_SCHEMA_LOCK_PATH, "SPDX JSON Schema lock"
    )
    license_path = _regular_file_without_symlinks(
        SPDX_SCHEMA_LICENSE_PATH, "SPDX JSON Schema license"
    )
    try:
        schema_lock = json.loads(lock_path.read_text(encoding="utf-8"))
        encoded_schema = schema_path.read_text(encoding="ascii")
        if not encoded_schema.endswith("\n") or any(
            character.isspace() for character in encoded_schema[:-1]
        ):
            raise RuntimeError("vendored SPDX JSON Schema encoding drifted")
        schema_bytes = base64.b64decode(encoded_schema[:-1], validate=True)
        schema = json.loads(schema_bytes)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("vendored SPDX JSON Schema could not be parsed") from exc
    if schema_lock.get("revision") != SPDX_SCHEMA_REVISION:
        raise RuntimeError("SPDX JSON Schema revision lock drifted")
    if schema_lock.get("sha256") != SPDX_SCHEMA_SHA256:
        raise RuntimeError("SPDX JSON Schema SHA-256 lock drifted")
    if hashlib.sha256(schema_bytes).hexdigest() != SPDX_SCHEMA_SHA256:
        raise RuntimeError("vendored SPDX JSON Schema bytes drifted")
    if schema_lock.get("path") != "schemas/spdx-schema.json":
        raise RuntimeError("SPDX JSON Schema source path drifted")
    if schema_lock.get("vendored_path") != "replacement/spdx-2.3.schema.json.b64":
        raise RuntimeError("SPDX JSON Schema vendored path drifted")
    if schema_lock.get("vendored_encoding") != "base64":
        raise RuntimeError("SPDX JSON Schema vendored encoding drifted")
    if schema_lock.get("license") != "CC-BY-3.0":
        raise RuntimeError("SPDX JSON Schema license identifier drifted")
    if schema_lock.get("license_path") != (
        "LICENSES/SPDX-spdx-spec-CC-BY-3.0.txt"
    ):
        raise RuntimeError("SPDX JSON Schema license path drifted")
    license_bytes = license_path.read_bytes()
    if hashlib.sha256(license_bytes).hexdigest() != SPDX_SCHEMA_LICENSE_SHA256:
        raise RuntimeError("vendored SPDX JSON Schema license bytes drifted")
    if not license_bytes.endswith(b"\n") or hashlib.sha256(
        license_bytes[:-1]
    ).hexdigest() != SPDX_SCHEMA_UPSTREAM_LICENSE_SHA256:
        raise RuntimeError("SPDX JSON Schema upstream license provenance drifted")
    if schema_lock.get("vendored_license_sha256") != SPDX_SCHEMA_LICENSE_SHA256:
        raise RuntimeError("SPDX JSON Schema vendored license lock drifted")
    if schema_lock.get("upstream_license_sha256") != (
        SPDX_SCHEMA_UPSTREAM_LICENSE_SHA256
    ):
        raise RuntimeError("SPDX JSON Schema upstream license lock drifted")
    if schema_lock.get("generator") != _pinned_sbom_identity()["generator"]:
        raise RuntimeError("SPDX generator identity lock drifted")
    if schema_lock.get("validator_runtime") != _pinned_sbom_identity()["validator"]:
        raise RuntimeError("SPDX validator runtime lock drifted")
    source_url = _https_url(schema_lock.get("source_url"), "SPDX schema source URL")
    expected_source_url = (
        "https://raw.githubusercontent.com/spdx/spdx-spec/"
        f"{SPDX_SCHEMA_REVISION}/schemas/spdx-schema.json"
    )
    if source_url != expected_source_url:
        raise RuntimeError("SPDX JSON Schema source URL is not revision-pinned")
    if _https_url(schema_lock.get("repository"), "SPDX schema repository") != (
        "https://github.com/spdx/spdx-spec.git"
    ):
        raise RuntimeError("SPDX JSON Schema repository drifted")
    if schema.get("$schema") != schema_lock.get("json_schema_draft"):
        raise RuntimeError("vendored SPDX JSON Schema draft drifted")
    return schema, schema_lock


def sbom_readiness() -> tuple[bool, dict]:
    """Report nonsecret readiness for deterministic offline SPDX generation."""

    identity = _pinned_sbom_identity()
    details = {
        "status": "PINNED_OFFLINE_SPDX_2_3",
        "ready": False,
        **identity,
        "observed_validator": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "jsonschema_version": None,
            "pyyaml_version": None,
        },
        "schema_lock_sha256": None,
        "detail": None,
    }
    try:
        schema, _ = _load_pinned_schema()
        details["schema_lock_sha256"] = sha256_file(SPDX_SCHEMA_LOCK_PATH)
    except RuntimeError as exc:
        details["detail"] = str(exc)
        return False, details
    try:
        import jsonschema
        import yaml  # noqa: F401
    except ImportError:
        details["detail"] = "offline SPDX validator dependency is unavailable"
        return False, details
    try:
        details["observed_validator"]["jsonschema_version"] = (
            importlib.metadata.version("jsonschema")
        )
        details["observed_validator"]["pyyaml_version"] = importlib.metadata.version(
            "PyYAML"
        )
    except importlib.metadata.PackageNotFoundError:
        details["detail"] = "offline SPDX validator package metadata is unavailable"
        return False, details

    expected = identity["validator"]
    if details["observed_validator"] != expected:
        details["detail"] = "offline SPDX validator runtime version mismatch"
        return False, details
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError:
        details["detail"] = "vendored SPDX JSON Schema is invalid"
        return False, details
    details["ready"] = True
    details["detail"] = "pinned schema, license, generator, and validator verified"
    return True, details


def verified_sbom_identity() -> dict:
    ready, readiness = sbom_readiness()
    if not ready:
        raise RuntimeError(readiness["detail"])
    return {
        "generator": readiness["generator"],
        "schema": readiness["schema"],
        "validator": readiness["validator"],
        "schema_lock_sha256": readiness["schema_lock_sha256"],
    }


def validate_official_spdx_schema(document: dict) -> None:
    """Validate against the byte-pinned official SPDX v2.3 Draft-07 schema."""

    ready, readiness = sbom_readiness()
    if not ready:
        raise RuntimeError(readiness["detail"])
    import jsonschema

    schema, _ = _load_pinned_schema()
    validator = jsonschema.Draft7Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.absolute_path) or "document"
        raise RuntimeError(f"SPDX 2.3 schema validation failed at {path}: {first.message}")


def write_validated_spdx(path: Path, document: dict) -> dict[str, object]:
    """Validate, atomically write, reread, and validate one SPDX document."""

    validate_spdx_document(document)
    content = spdx_json_bytes(document)
    path = reject_symlink_ancestors(path, "SBOM output path")
    temporary = path.with_name(f".{path.name}.tmp")
    reject_symlink_ancestors(temporary, "SBOM atomic temporary path")
    if path.exists() or temporary.exists():
        raise RuntimeError("SBOM output or atomic temporary path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o644)
        if temporary.read_bytes() != content:
            raise RuntimeError("SBOM atomic temporary bytes drifted")
        validate_spdx_document(json.loads(temporary.read_text(encoding="utf-8")))
        os.replace(temporary, path)
        observed = path.read_bytes()
        if observed != content:
            raise RuntimeError("SBOM bytes drifted after atomic write")
        validate_spdx_document(json.loads(observed))
        identity = verified_sbom_identity()
        return {
            "format": "SPDX-2.3 JSON",
            "path": SPDX_FILENAME,
            "bytes": len(observed),
            "sha256": hashlib.sha256(observed).hexdigest(),
            "document_namespace": document["documentNamespace"],
            "schema_revision": SPDX_SCHEMA_REVISION,
            "schema_sha256": SPDX_SCHEMA_SHA256,
            "generator": identity["generator"],
            "validator": identity["validator"],
            "schema_lock_sha256": identity["schema_lock_sha256"],
        }
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def deterministic_spdx_sbom(
    *,
    artifact_root: Path,
    artifacts: dict,
    replacement: dict,
    source_receipt: dict,
    source_receipt_sha256: str,
    toolchain: dict,
    toolchain_lock_sha256: str,
    pre_ncs: dict,
    post_ncs: dict,
    active_projects_path: Path,
    container_declaration_matched: object,
    source_date_epoch: object,
) -> dict:
    """Return a deterministic SPDX 2.3 JSON document or fail closed."""

    source = _validate_source(
        replacement,
        source_receipt,
        source_receipt_sha256,
        toolchain_lock_sha256,
    )
    projects, manifests, project_locations = _validate_ncs(
        toolchain, pre_ncs, post_ncs, active_projects_path
    )
    container = _validate_container(toolchain, container_declaration_matched)
    validated_artifacts = _validate_artifacts(artifact_root, artifacts)
    source_date_epoch, created = _source_date_timestamp(source_date_epoch)
    sbom_identity = verified_sbom_identity()

    main_package = _package(
        spdx_id=SPDX_MAIN_PACKAGE_ID,
        name="Anticipy Pendant Firmware Candidate",
        version=(
            "candidate-" + validated_artifacts["zephyr.uf2"]["sha256"][:16]
        ),
        download_location="NOASSERTION",
        purpose="FIRMWARE",
        comment=(
            "Candidate only; not signed, flash-approved, flashed, or physically "
            "verified. Canonical active west project snapshot "
            f"{manifests['active_projects_frozen_filename']} SHA-256: "
            f"{manifests['active_projects_frozen_sha256']}; project count: "
            f"{manifests['active_projects_frozen_project_count']}; nrf/west.yml "
            f"SHA-256: {manifests['nrf_west_yml_sha256']}; .west/config SHA-256: "
            f"{manifests['west_config_sha256']}. SOURCE_DATE_EPOCH: "
            f"{source_date_epoch}."
        ),
        external_refs=[
            {
                "referenceCategory": "OTHER",
                "referenceType": "west-active-projects-frozen-sha256",
                "referenceLocator": manifests["active_projects_frozen_sha256"],
            },
            {
                "referenceCategory": "OTHER",
                "referenceType": "west-active-projects-frozen-project-count",
                "referenceLocator": str(
                    manifests["active_projects_frozen_project_count"]
                ),
            },
            {
                "referenceCategory": "OTHER",
                "referenceType": "nrf-west-yml-sha256",
                "referenceLocator": manifests["nrf_west_yml_sha256"],
            },
            {
                "referenceCategory": "OTHER",
                "referenceType": "west-config-sha256",
                "referenceLocator": manifests["west_config_sha256"],
            },
        ],
    )
    source_package = _package(
        spdx_id=SPDX_SOURCE_PACKAGE_ID,
        name="Anticipy Omi v2.0.1 Source Overlay",
        version=source["commit"],
        download_location=source["repository"],
        purpose="SOURCE",
        comment=(
            f"Locked upstream commit {source['commit']}; patch SHA-256 "
            f"{source['patch_sha256']}; materialized content-tree SHA-256 "
            f"{source['content_tree_sha256']}; deterministic source receipt SHA-256 "
            f"{source['source_receipt_sha256']}."
        ),
        external_refs=[
            {
                "referenceCategory": "OTHER",
                "referenceType": "vcs",
                "referenceLocator": (
                    f"git+{source['repository']}@{source['commit']}"
                ),
            },
            {
                "referenceCategory": "OTHER",
                "referenceType": "content-tree-sha256",
                "referenceLocator": source["content_tree_sha256"],
            },
            {
                "referenceCategory": "OTHER",
                "referenceType": "source-receipt-sha256",
                "referenceLocator": source["source_receipt_sha256"],
            },
        ],
    )
    toolchain_package = _package(
        spdx_id=SPDX_TOOLCHAIN_PACKAGE_ID,
        name=container["image"],
        version=container["digest"],
        download_location="https://docker.io/",
        purpose="CONTAINER",
        comment=(
            f"Platform {container['platform']}; OCI digest was supplied as an "
            "UNVERIFIED_OPERATOR_DECLARATION and is not independent execution "
            f"attestation. Toolchain lock SHA-256: {source['toolchain_lock_sha256']}."
        ),
        external_refs=[
            {
                "referenceCategory": "OTHER",
                "referenceType": "oci-digest",
                "referenceLocator": container["digest"],
            }
        ],
    )

    project_packages: list[dict] = []
    project_ids: dict[str, str] = {}
    for path, commit in projects.items():
        package_id = "SPDXRef-Package-West-" + canonical_json_sha256(
            {"commit": commit, "path": path}
        )[:20]
        project_ids[path] = package_id
        repository = project_locations.get(path)
        if repository is None:
            raise RuntimeError("west project has no immutable HTTPS repository")
        locator = f"git+{repository}@{commit}"
        project_packages.append(
            _package(
                spdx_id=package_id,
                name=f"west:{path}",
                version=commit,
                download_location=repository,
                purpose="SOURCE",
                comment=(
                    "Exact clean active west project commit bound by canonical "
                    f"snapshot {manifests['active_projects_frozen_sha256']}."
                ),
                external_refs=[
                    {
                        "referenceCategory": "OTHER",
                        "referenceType": "vcs",
                        "referenceLocator": locator,
                    }
                ],
            )
        )

    files: list[dict] = []
    artifact_ids: dict[str, str] = {}
    for name, record in validated_artifacts.items():
        file_id = "SPDXRef-File-" + canonical_json_sha256(
            {"name": name, "sha256": record["sha256"]}
        )[:20]
        artifact_ids[name] = file_id
        files.append(
            {
                "SPDXID": file_id,
                "fileName": f"./zephyr/{name}",
                "fileTypes": [record["file_type"]],
                "checksums": _spdx_checksum(record["sha256"]),
                "licenseConcluded": "NOASSERTION",
                "licenseInfoInFiles": ["NOASSERTION"],
                "copyrightText": "NOASSERTION",
                "comment": f"Built artifact size: {record['bytes']} bytes.",
            }
        )

    relationships = [
        {
            "spdxElementId": SPDX_MAIN_PACKAGE_ID,
            "relationshipType": "GENERATED_FROM",
            "relatedSpdxElement": SPDX_SOURCE_PACKAGE_ID,
        },
        {
            "spdxElementId": SPDX_TOOLCHAIN_PACKAGE_ID,
            "relationshipType": "BUILD_TOOL_OF",
            "relatedSpdxElement": SPDX_MAIN_PACKAGE_ID,
        },
    ]
    relationships.extend(
        {
            "spdxElementId": project_ids[path],
            "relationshipType": "BUILD_DEPENDENCY_OF",
            "relatedSpdxElement": SPDX_MAIN_PACKAGE_ID,
            "comment": (
                "Build input recorded from the canonical active west project "
                "snapshot; this does "
                "not claim the entire repository is linked into the firmware."
            ),
        }
        for path in sorted(project_ids)
    )
    relationships.extend(
        {
            "spdxElementId": SPDX_MAIN_PACKAGE_ID,
            "relationshipType": "GENERATES",
            "relatedSpdxElement": artifact_ids[name],
        }
        for name in sorted(artifact_ids)
    )

    document = {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": SPDX_DATA_LICENSE,
        "SPDXID": SPDX_DOCUMENT_ID,
        "name": "Anticipy Pendant Firmware Candidate SBOM",
        "creationInfo": {
            "created": created,
            "creators": [
                f"Tool: {SBOM_GENERATOR_NAME}-{SBOM_GENERATOR_VERSION}",
                f"Tool: CPython-{SBOM_PYTHON_VERSION}",
                f"Tool: jsonschema-{SBOM_JSONSCHEMA_VERSION}",
                f"Tool: PyYAML-{SBOM_PYYAML_VERSION}",
            ],
            "comment": (
                f"Created is derived from deterministic SOURCE_DATE_EPOCH "
                f"{source_date_epoch}, not the host wall clock. Build execution "
                "provenance remains external. Validated with official schema "
                f"{SPDX_SCHEMA_REVISION}/{SPDX_SCHEMA_SHA256} using CPython "
                f"{SBOM_PYTHON_VERSION}, jsonschema {SBOM_JSONSCHEMA_VERSION}, "
                f"and PyYAML {SBOM_PYYAML_VERSION}. Schema lock SHA-256: "
                f"{sbom_identity['schema_lock_sha256']}."
            ),
        },
        "documentDescribes": [SPDX_MAIN_PACKAGE_ID],
        "packages": [
            main_package,
            source_package,
            toolchain_package,
            *sorted(project_packages, key=lambda package: package["SPDXID"]),
        ],
        "files": sorted(files, key=lambda file: file["SPDXID"]),
        "relationships": sorted(
            relationships,
            key=lambda relationship: (
                relationship["spdxElementId"],
                relationship["relationshipType"],
                relationship["relatedSpdxElement"],
            ),
        ),
    }
    document["documentNamespace"] = (
        "https://spdx.org/spdxdocs/anticipy-pendant-firmware-"
        + canonical_json_sha256(document)
    )
    validate_spdx_document(document)
    return document
