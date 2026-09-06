from __future__ import annotations

import builtins
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = FIRMWARE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import spdx_sbom as sbom  # noqa: E402
from build_candidate import build, hash_artifacts, probe  # noqa: E402
from materialize_replacement import deterministic_receipt, sha256_file  # noqa: E402


REPLACEMENT_LOCK = FIRMWARE_ROOT / "replacement" / "replacement.lock.json"
TOOLCHAIN_LOCK = FIRMWARE_ROOT / "replacement" / "toolchain.lock.json"
SOURCE_DATE_EPOCH = 1_728_134_730


class FirmwareSBOMFixture(unittest.TestCase):
    def setUp(self) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        self.temporary = Path(
            tempfile.mkdtemp(prefix="spdx-test-", dir=FIRMWARE_ROOT / ".build")
        )
        self.artifact_root = self.temporary / "artifacts"
        (self.artifact_root / "zephyr").mkdir(parents=True)
        self.replacement = json.loads(REPLACEMENT_LOCK.read_text(encoding="utf-8"))
        self.toolchain = json.loads(TOOLCHAIN_LOCK.read_text(encoding="utf-8"))
        self.source_receipt = deterministic_receipt(
            self.replacement,
            self.replacement["materialized_source"]["critical_file_sha256"],
        )
        self.source_receipt_sha256 = self.replacement["materialized_source"][
            "source_receipt_sha256"
        ]
        self.toolchain_lock_sha256 = sha256_file(TOOLCHAIN_LOCK)
        self.project_commits = {
            "modules/sample": "a" * 40,
            "nrf": self.toolchain["nrf_connect_sdk"]["commit"],
            "zephyr": self.toolchain["zephyr"]["commit"],
        }
        self.project_repositories = {
            "modules/sample": "https://example.invalid/sample.git",
            "nrf": self.toolchain["nrf_connect_sdk"]["repository"],
            "zephyr": self.toolchain["zephyr"]["repository"],
        }
        self.active_projects = (
            self.artifact_root / "west-active-projects-frozen.tsv"
        )
        self._write_active_snapshot()
        self.artifacts = self._write_artifacts()
        self.pre_ncs = self._snapshot(self.project_commits)
        self.post_ncs = json.loads(json.dumps(self.pre_ncs))

    def tearDown(self) -> None:
        shutil.rmtree(self.temporary, ignore_errors=True)

    def _write_active_snapshot(
        self,
        *,
        sample_path: str = "modules/sample",
        include_sample: bool = True,
        extra_project: bool = False,
        sample_commit: str = "a" * 40,
        sort_rows: bool = True,
        final_newline: bool = True,
    ) -> None:
        projects: list[tuple[str, str]] = []
        if include_sample:
            projects.append((sample_path, sample_commit))
        projects.append(("nrf", self.toolchain["nrf_connect_sdk"]["commit"]))
        projects.append(("zephyr", self.toolchain["zephyr"]["commit"]))
        if extra_project:
            projects.append(("modules/extra", "b" * 40))
        if sort_rows:
            projects.sort()
        else:
            projects.sort(reverse=True)
        content = "".join(f"{path}\t{commit}\n" for path, commit in projects)
        if not final_newline:
            content = content.removesuffix("\n")
        self.active_projects.write_text(content, encoding="utf-8")

    def _write_artifacts(self) -> dict[str, dict[str, object]]:
        records: dict[str, dict[str, object]] = {}
        content = {
            "zephyr.elf": b"ELF candidate\x00",
            "zephyr.hex": b":020000040000FA\n",
            "zephyr.bin": b"binary candidate\x00",
            "zephyr.uf2": b"UF2 candidate\x00",
            "zephyr.map": b"map candidate\n",
        }
        for name, value in content.items():
            path = self.artifact_root / "zephyr" / name
            path.write_bytes(value)
            records[name] = {
                "bytes": len(value),
                "sha256": hashlib.sha256(value).hexdigest(),
            }
        return records

    def _snapshot(self, projects: dict[str, str]) -> dict:
        active_sha256 = hashlib.sha256(
            self.active_projects.read_bytes()
        ).hexdigest()
        projects = dict(projects)
        return {
            "project_commits": projects,
            "project_count": len(projects),
            "project_commits_sha256": sbom.canonical_json_sha256(projects),
            "project_repositories": dict(self.project_repositories),
            "project_repositories_sha256": sbom.canonical_json_sha256(
                self.project_repositories
            ),
            "ncs_commit": projects.get("nrf"),
            "zephyr_commit": projects.get("zephyr"),
            "west_manifest_sha256": self.toolchain["nrf_connect_sdk"][
                "west_manifest_sha256"
            ],
            "west_config_sha256": "c" * 64,
            "active_projects_frozen_filename": (
                "west-active-projects-frozen.tsv"
            ),
            "active_projects_frozen_sha256": active_sha256,
            "active_projects_frozen_project_count": len(projects),
        }

    def generate(self, **overrides) -> dict:
        arguments = {
            "artifact_root": self.artifact_root,
            "artifacts": self.artifacts,
            "replacement": self.replacement,
            "source_receipt": self.source_receipt,
            "source_receipt_sha256": self.source_receipt_sha256,
            "toolchain": self.toolchain,
            "toolchain_lock_sha256": self.toolchain_lock_sha256,
            "pre_ncs": self.pre_ncs,
            "post_ncs": self.post_ncs,
            "active_projects_path": self.active_projects,
            "container_declaration_matched": True,
            "source_date_epoch": SOURCE_DATE_EPOCH,
        }
        arguments.update(overrides)
        return sbom.deterministic_spdx_sbom(**arguments)


class FirmwareSBOMTests(FirmwareSBOMFixture):
    def _probe_with_non_sbom_inputs_ready(self) -> dict:
        expected_digest = self.toolchain["toolchain_container"]["digest"]
        with (
            mock.patch("build_candidate.source_status", return_value=(True, "ok")),
            mock.patch("build_candidate.ncs_status", return_value=(True, {})),
            mock.patch(
                "build_candidate.tool_paths",
                return_value=(
                    {
                        "west": "/fixture/west",
                        "cmake": "/fixture/cmake",
                        "ninja": "/fixture/ninja",
                        "arm_compiler": "/fixture/compiler",
                    },
                    "/fixture/compiler",
                ),
            ),
            mock.patch.dict(
                os.environ,
                {"ANTICIPY_TOOLCHAIN_IMAGE_DIGEST": expected_digest},
                clear=False,
            ),
        ):
            return probe(self.temporary / "source", self.temporary / "ncs")

    def test_probe_requires_exact_offline_sbom_runtime(self) -> None:
        ready, readiness = sbom.sbom_readiness()
        self.assertTrue(ready, readiness["detail"])
        self.assertEqual(readiness["generator"]["version"], "1.0.0")
        self.assertEqual(readiness["observed_validator"], readiness["validator"])
        self.assertRegex(readiness["schema_lock_sha256"], r"^[0-9a-f]{64}$")

        expected_digest = self.toolchain["toolchain_container"]["digest"]
        unavailable = {
            "status": "PINNED_OFFLINE_SPDX_2_3",
            "ready": False,
            "detail": "offline SPDX validator dependency is unavailable",
        }
        with (
            mock.patch("build_candidate.source_status", return_value=(True, "ok")),
            mock.patch("build_candidate.ncs_status", return_value=(True, {})),
            mock.patch(
                "build_candidate.tool_paths",
                return_value=(
                    {
                        "west": "/fixture/west",
                        "cmake": "/fixture/cmake",
                        "ninja": "/fixture/ninja",
                        "arm_compiler": "/fixture/compiler",
                    },
                    "/fixture/compiler",
                ),
            ),
            mock.patch("build_candidate.sbom_readiness", return_value=(False, unavailable)),
            mock.patch.dict(
                os.environ,
                {"ANTICIPY_TOOLCHAIN_IMAGE_DIGEST": expected_digest},
                clear=False,
            ),
        ):
            status = probe(self.temporary / "source", self.temporary / "ncs")
        self.assertFalse(status["ready"])
        self.assertEqual(status["sbom"], unavailable)

        with mock.patch.object(sbom.platform, "python_version", return_value="0.0.0"):
            ready, mismatch = sbom.sbom_readiness()
        self.assertFalse(ready)
        self.assertIn("version mismatch", mismatch["detail"])

    def test_probe_fails_for_each_asset_dependency_and_version_drift(self) -> None:
        schema_copy = self.temporary / "schema.b64"
        schema_copy.write_bytes(sbom.SPDX_SCHEMA_PATH.read_bytes() + b"drift")
        with mock.patch.object(sbom, "SPDX_SCHEMA_PATH", schema_copy):
            status = self._probe_with_non_sbom_inputs_ready()
        self.assertFalse(status["ready"])
        self.assertFalse(status["sbom"]["ready"])

        lock = json.loads(sbom.SPDX_SCHEMA_LOCK_PATH.read_text(encoding="utf-8"))
        lock["revision"] = "0" * 40
        lock_copy = self.temporary / "schema.lock.json"
        lock_copy.write_text(json.dumps(lock), encoding="utf-8")
        with mock.patch.object(sbom, "SPDX_SCHEMA_LOCK_PATH", lock_copy):
            status = self._probe_with_non_sbom_inputs_ready()
        self.assertFalse(status["ready"])
        self.assertFalse(status["sbom"]["ready"])

        license_copy = self.temporary / "LICENSE"
        license_copy.write_bytes(sbom.SPDX_SCHEMA_LICENSE_PATH.read_bytes() + b"drift")
        with mock.patch.object(sbom, "SPDX_SCHEMA_LICENSE_PATH", license_copy):
            status = self._probe_with_non_sbom_inputs_ready()
        self.assertFalse(status["ready"])
        self.assertFalse(status["sbom"]["ready"])

        real_import = builtins.__import__

        for missing_package in ("jsonschema", "yaml"):
            with self.subTest(missing=missing_package):
                def missing_dependency(name, *args, **kwargs):
                    if name == missing_package:
                        raise ImportError("missing for test")
                    return real_import(name, *args, **kwargs)

                with mock.patch(
                    "builtins.__import__", side_effect=missing_dependency
                ):
                    status = self._probe_with_non_sbom_inputs_ready()
                self.assertFalse(status["ready"])
                self.assertIn("unavailable", status["sbom"]["detail"])

        version_cases = (
            ("python", None),
            ("jsonschema", "jsonschema"),
            ("pyyaml", "PyYAML"),
        )
        real_version = importlib.metadata.version
        for label, package in version_cases:
            with self.subTest(version=label):
                if package is None:
                    patches = [
                        mock.patch.object(
                            sbom.platform, "python_version", return_value="0.0.0"
                        )
                    ]
                else:
                    patches = [
                        mock.patch.object(
                            sbom.importlib.metadata,
                            "version",
                            side_effect=lambda name, target=package: (
                                "0.0.0" if name == target else real_version(name)
                            ),
                        )
                    ]
                with patches[0]:
                    status = self._probe_with_non_sbom_inputs_ready()
                self.assertFalse(status["ready"])
                self.assertIn("version mismatch", status["sbom"]["detail"])

    def test_official_schema_valid_document_is_deterministic_and_host_free(self) -> None:
        first = self.generate()
        first_bytes = sbom.spdx_json_bytes(first)

        second_root = self.temporary / "different-root"
        shutil.copytree(self.artifact_root, second_root)
        reversed_artifacts = dict(reversed(list(self.artifacts.items())))
        reversed_projects = dict(reversed(list(self.project_commits.items())))
        second_snapshot = self._snapshot(reversed_projects)
        second = self.generate(
            artifact_root=second_root,
            artifacts=reversed_artifacts,
            pre_ncs=second_snapshot,
            post_ncs=json.loads(json.dumps(second_snapshot)),
            active_projects_path=second_root / "west-active-projects-frozen.tsv",
        )

        self.assertEqual(first, second)
        self.assertEqual(first_bytes, sbom.spdx_json_bytes(second))
        rendered = first_bytes.decode("utf-8")
        self.assertNotIn(str(self.temporary), rendered)
        self.assertNotIn(str(Path.home()), rendered)
        self.assertEqual(first["spdxVersion"], "SPDX-2.3")
        self.assertEqual(first["dataLicense"], "CC0-1.0")
        self.assertEqual(first["creationInfo"]["created"], "2024-10-05T13:25:30Z")
        self.assertEqual(
            first["creationInfo"]["creators"],
            [
                "Tool: anticipy-firmware-spdx-1.0.0",
                "Tool: CPython-3.10.14",
                "Tool: jsonschema-4.26.0",
                "Tool: PyYAML-6.0.3",
            ],
        )

        mutated = json.loads(json.dumps(first))
        mutated["packages"][0]["comment"] += " altered"
        with self.assertRaisesRegex(RuntimeError, "namespace does not bind"):
            sbom.validate_spdx_document(mutated)
        body = dict(mutated)
        body.pop("documentNamespace")
        changed_namespace = (
            "https://spdx.org/spdxdocs/anticipy-pendant-firmware-"
            + sbom.canonical_json_sha256(body)
        )
        self.assertNotEqual(first["documentNamespace"], changed_namespace)

        generator_changed = json.loads(json.dumps(first))
        generator_changed["creationInfo"]["creators"][0] = (
            "Tool: anticipy-firmware-spdx-1.0.1"
        )
        body = dict(generator_changed)
        body.pop("documentNamespace")
        generator_namespace = (
            "https://spdx.org/spdxdocs/anticipy-pendant-firmware-"
            + sbom.canonical_json_sha256(body)
        )
        self.assertNotEqual(first["documentNamespace"], generator_namespace)

    def test_document_completely_binds_sources_build_inputs_and_artifacts(self) -> None:
        document = self.generate()
        packages = {package["name"]: package for package in document["packages"]}
        self.assertIn("Anticipy Pendant Firmware Candidate", packages)
        self.assertIn("Anticipy Omi v2.0.1 Source Overlay", packages)
        self.assertIn(self.toolchain["toolchain_container"]["image"], packages)
        main = packages["Anticipy Pendant Firmware Candidate"]
        evidence = {
            reference["referenceType"]: reference["referenceLocator"]
            for reference in main["externalRefs"]
        }
        active_sha256 = hashlib.sha256(
            self.active_projects.read_bytes()
        ).hexdigest()
        self.assertEqual(
            evidence,
            {
                "west-active-projects-frozen-sha256": active_sha256,
                "west-active-projects-frozen-project-count": "3",
                "nrf-west-yml-sha256": self.toolchain["nrf_connect_sdk"][
                    "west_manifest_sha256"
                ],
                "west-config-sha256": "c" * 64,
            },
        )
        for project in self.project_commits:
            self.assertIn(f"west:{project}", packages)
            package = packages[f"west:{project}"]
            self.assertTrue(package["downloadLocation"].startswith("https://"))
            self.assertTrue(
                package["externalRefs"][0]["referenceLocator"].startswith(
                    "git+https://"
                )
            )
            self.assertNotIn("west-path:", json.dumps(package))
        container = packages[self.toolchain["toolchain_container"]["image"]]
        self.assertIn("UNVERIFIED_OPERATOR_DECLARATION", container["comment"])
        self.assertFalse(container["filesAnalyzed"])

        files = {Path(file["fileName"]).name: file for file in document["files"]}
        self.assertEqual(set(files), set(self.artifacts))
        for name, record in self.artifacts.items():
            self.assertEqual(
                files[name]["checksums"],
                [{"algorithm": "SHA256", "checksumValue": record["sha256"]}],
            )
        build_inputs = {
            relationship["spdxElementId"]
            for relationship in document["relationships"]
            if relationship["relationshipType"] == "BUILD_DEPENDENCY_OF"
        }
        project_ids = {
            package["SPDXID"]
            for name, package in packages.items()
            if name.startswith("west:")
        }
        self.assertEqual(build_inputs, project_ids)
        self.assertTrue(
            all(
                relationship["relationshipType"] != "DEPENDS_ON"
                for relationship in document["relationships"]
            )
        )

    def test_artifact_mutation_symlink_and_empty_inventory_fail_closed(self) -> None:
        (self.artifact_root / "zephyr" / "zephyr.uf2").write_bytes(b"mutated")
        with self.assertRaisesRegex(RuntimeError, "artifact bytes drifted"):
            self.generate()

        self.artifacts = self._write_artifacts()
        target = self.artifact_root / "zephyr" / "zephyr.hex"
        target.unlink()
        target.symlink_to("zephyr.uf2")
        with self.assertRaisesRegex(RuntimeError, "traverse a symlink"):
            self.generate()

        with self.assertRaisesRegex(RuntimeError, "requires zephyr.uf2"):
            self.generate(artifacts={})
        self.assertFalse((self.artifact_root / sbom.SPDX_FILENAME).exists())

    def test_active_snapshot_membership_revision_and_path_fail_closed(self) -> None:
        cases = (
            ("missing", {"include_sample": False}, "count is inconsistent"),
            ("extra", {"extra_project": True}, "count is inconsistent"),
            ("escape", {"sample_path": "../sample"}, "relative and normalized"),
            ("commit", {"sample_commit": "A" * 40}, "40-character Git commit"),
        )
        for label, snapshot_arguments, message in cases:
            with self.subTest(label=label):
                self._write_active_snapshot(**snapshot_arguments)
                snapshot = self._snapshot(self.project_commits)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.generate(pre_ncs=snapshot, post_ncs=snapshot)
                self._write_active_snapshot()

    def test_active_snapshot_sort_duplicate_newline_and_repository_fail_closed(
        self,
    ) -> None:
        self._write_active_snapshot(sort_rows=False)
        snapshot = self._snapshot(self.project_commits)
        with self.assertRaisesRegex(RuntimeError, "not sorted"):
            self.generate(pre_ncs=snapshot, post_ncs=snapshot)
        self._write_active_snapshot()

        content = self.active_projects.read_text(encoding="utf-8")
        self.active_projects.write_text(
            content + content.splitlines(keepends=True)[0],
            encoding="utf-8",
        )
        snapshot = self._snapshot(self.project_commits)
        with self.assertRaisesRegex(RuntimeError, "duplicate project path"):
            self.generate(pre_ncs=snapshot, post_ncs=snapshot)
        self._write_active_snapshot(final_newline=False)
        snapshot = self._snapshot(self.project_commits)
        with self.assertRaisesRegex(RuntimeError, "not canonical TSV"):
            self.generate(pre_ncs=snapshot, post_ncs=snapshot)
        self._write_active_snapshot()

        self.active_projects.write_bytes(b"nrf\t" + b"a" * 40 + b"\xff\n")
        snapshot = self._snapshot(self.project_commits)
        with self.assertRaisesRegex(RuntimeError, "not UTF-8"):
            self.generate(pre_ncs=snapshot, post_ncs=snapshot)
        self._write_active_snapshot()

        credentialed = json.loads(json.dumps(self.pre_ncs))
        credentialed["project_repositories"]["modules/sample"] = (
            "https://user:secret@example.invalid/sample.git"
        )
        credentialed["project_repositories_sha256"] = sbom.canonical_json_sha256(
            credentialed["project_repositories"]
        )
        with self.assertRaisesRegex(RuntimeError, "credential-free"):
            self.generate(pre_ncs=credentialed, post_ncs=credentialed)

        whitespace = json.loads(json.dumps(self.pre_ncs))
        whitespace["project_repositories"]["modules/sample"] = (
            "https://example.invalid/sample repo.git"
        )
        whitespace["project_repositories_sha256"] = sbom.canonical_json_sha256(
            whitespace["project_repositories"]
        )
        with self.assertRaisesRegex(RuntimeError, "credential-free"):
            self.generate(pre_ncs=whitespace, post_ncs=whitespace)

        missing = json.loads(json.dumps(self.pre_ncs))
        missing["project_repositories"].pop("modules/sample")
        missing["project_repositories_sha256"] = sbom.canonical_json_sha256(
            missing["project_repositories"]
        )
        with self.assertRaisesRegex(RuntimeError, "does not match projects"):
            self.generate(pre_ncs=missing, post_ncs=missing)

        changed = json.loads(json.dumps(self.post_ncs))
        changed["project_commits"]["modules/sample"] = "b" * 40
        changed["project_commits_sha256"] = sbom.canonical_json_sha256(
            changed["project_commits"]
        )
        with self.assertRaisesRegex(RuntimeError, "changed during the build"):
            self.generate(post_ncs=changed)

    def test_pre_post_manifest_config_snapshot_and_repository_drift_fail_closed(
        self,
    ) -> None:
        cases = (
            (
                "west-config",
                {"west_config_sha256": "d" * 64},
                r"\.west/config changed during the build",
            ),
            (
                "west-manifest",
                {"west_manifest_sha256": "d" * 64},
                "post-build NCS west.yml SHA-256 drifted",
            ),
            (
                "active-snapshot",
                {"active_projects_frozen_sha256": "d" * 64},
                "active west project snapshot SHA-256 drifted",
            ),
            (
                "active-count",
                {"active_projects_frozen_project_count": 99},
                "snapshot count is inconsistent",
            ),
        )
        for label, changes, message in cases:
            with self.subTest(label=label):
                changed = json.loads(json.dumps(self.post_ncs))
                changed.update(changes)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.generate(post_ncs=changed)

        changed = json.loads(json.dumps(self.post_ncs))
        changed["project_repositories"]["modules/sample"] = (
            "https://example.invalid/changed.git"
        )
        changed["project_repositories_sha256"] = sbom.canonical_json_sha256(
            changed["project_repositories"]
        )
        with self.assertRaisesRegex(RuntimeError, "repositories changed"):
            self.generate(post_ncs=changed)

    def test_schema_drift_invalid_schema_and_missing_validator_fail_closed(self) -> None:
        missing = self.temporary / "missing-schema.b64"
        with mock.patch.object(sbom, "SPDX_SCHEMA_PATH", missing):
            with self.assertRaisesRegex(RuntimeError, "is missing"):
                self.generate()

        invalid_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": 4,
        }
        invalid_bytes = json.dumps(invalid_schema, separators=(",", ":")).encode()
        invalid_path = self.temporary / "invalid-schema.b64"
        import base64

        invalid_path.write_text(
            base64.b64encode(invalid_bytes).decode("ascii") + "\n",
            encoding="ascii",
        )
        invalid_hash = hashlib.sha256(invalid_bytes).hexdigest()
        lock = json.loads(sbom.SPDX_SCHEMA_LOCK_PATH.read_text(encoding="utf-8"))
        lock["sha256"] = invalid_hash
        invalid_lock = self.temporary / "invalid-schema.lock.json"
        invalid_lock.write_text(json.dumps(lock), encoding="utf-8")
        with (
            mock.patch.object(sbom, "SPDX_SCHEMA_PATH", invalid_path),
            mock.patch.object(sbom, "SPDX_SCHEMA_LOCK_PATH", invalid_lock),
            mock.patch.object(sbom, "SPDX_SCHEMA_SHA256", invalid_hash),
        ):
            with self.assertRaisesRegex(RuntimeError, "is invalid"):
                self.generate()

        real_import = builtins.__import__

        def missing_jsonschema(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("missing for test")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=missing_jsonschema):
            with self.assertRaisesRegex(RuntimeError, "dependency is unavailable"):
                self.generate()

    def test_atomic_write_revalidates_and_cross_hashes_document(self) -> None:
        document = self.generate()
        path = self.artifact_root / sbom.SPDX_FILENAME
        record = sbom.write_validated_spdx(path, document)
        self.assertEqual(record["path"], sbom.SPDX_FILENAME)
        self.assertEqual(record["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(record["bytes"], path.stat().st_size)
        self.assertEqual(record["schema_sha256"], sbom.SPDX_SCHEMA_SHA256)
        self.assertFalse(path.with_name(f".{path.name}.tmp").exists())

        invalid = json.loads(json.dumps(document))
        invalid["unrecognized"] = True
        another = self.temporary / "invalid.spdx.json"
        with self.assertRaisesRegex(RuntimeError, "namespace does not bind"):
            sbom.write_validated_spdx(another, invalid)
        self.assertFalse(another.exists())

    def test_every_sensitive_path_rejects_symlinked_ancestors(self) -> None:
        artifact_link = self.temporary / "artifact-link"
        artifact_link.symlink_to(self.artifact_root, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "traverse a symlink"):
            self.generate(artifact_root=artifact_link)

        snapshot_link = self.temporary / "snapshot-link"
        snapshot_link.symlink_to(self.artifact_root, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "traverse a symlink"):
            self.generate(
                active_projects_path=snapshot_link / self.active_projects.name
            )

        document = self.generate()
        real_output = self.temporary / "real-output"
        real_output.mkdir()
        linked_output = self.temporary / "linked-output"
        linked_output.symlink_to(real_output, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "traverse a symlink"):
            sbom.write_validated_spdx(
                linked_output / "nested" / sbom.SPDX_FILENAME, document
            )

        assets = self.temporary / "schema-assets"
        assets.mkdir()
        schema_copy = assets / "schema.b64"
        lock_copy = assets / "schema.lock.json"
        license_copy = assets / "LICENSE"
        shutil.copy2(sbom.SPDX_SCHEMA_PATH, schema_copy)
        shutil.copy2(sbom.SPDX_SCHEMA_LOCK_PATH, lock_copy)
        shutil.copy2(sbom.SPDX_SCHEMA_LICENSE_PATH, license_copy)
        asset_link = self.temporary / "schema-link"
        asset_link.symlink_to(assets, target_is_directory=True)
        cases = (
            ("SPDX_SCHEMA_PATH", asset_link / schema_copy.name),
            ("SPDX_SCHEMA_LOCK_PATH", asset_link / lock_copy.name),
            ("SPDX_SCHEMA_LICENSE_PATH", asset_link / license_copy.name),
        )
        for attribute, path in cases:
            with self.subTest(attribute=attribute):
                with mock.patch.object(sbom, attribute, path):
                    ready, details = sbom.sbom_readiness()
                self.assertFalse(ready)
                self.assertIn("traverse a symlink", details["detail"])

    def test_parent_traversal_cannot_hide_symlinked_ancestor(self) -> None:
        real = self.temporary / "real"
        real.mkdir()
        linked = self.temporary / "linked"
        linked.symlink_to(real, target_is_directory=True)
        disguised = linked / ".." / "target"

        with self.assertRaisesRegex(RuntimeError, "parent traversal"):
            sbom.reject_symlink_ancestors(disguised, "disguised path")

    def test_hash_artifacts_rejects_symlinks_before_reading(self) -> None:
        outside = self.temporary / "outside-artifact.bin"
        outside.write_bytes(b"outside bytes must never be hashed")
        linked_artifact = self.artifact_root / "zephyr" / "zephyr.uf2"
        linked_artifact.unlink()
        linked_artifact.symlink_to(outside)

        with (
            mock.patch(
                "build_candidate.sha256_file",
                side_effect=AssertionError("artifact reader must not be called"),
            ) as reader,
            self.assertRaisesRegex(RuntimeError, "traverse a symlink"),
        ):
            hash_artifacts(self.artifact_root)
        reader.assert_not_called()

        linked_artifact.unlink()
        zephyr = self.artifact_root / "zephyr"
        moved = self.artifact_root / "real-zephyr"
        zephyr.rename(moved)
        zephyr.symlink_to(moved, target_is_directory=True)
        with (
            mock.patch(
                "build_candidate.sha256_file",
                side_effect=AssertionError("artifact reader must not be called"),
            ) as reader,
            self.assertRaisesRegex(RuntimeError, "traverse a symlink"),
        ):
            hash_artifacts(self.artifact_root)
        reader.assert_not_called()

    def test_hash_artifacts_rejects_nonregular_entry_before_reading(self) -> None:
        nonregular = self.artifact_root / "zephyr" / "zephyr.uf2"
        nonregular.unlink()
        nonregular.mkdir()

        with (
            mock.patch(
                "build_candidate.sha256_file",
                side_effect=AssertionError("artifact reader must not be called"),
            ) as reader,
            self.assertRaisesRegex(RuntimeError, "not a regular file"),
        ):
            hash_artifacts(self.artifact_root)
        reader.assert_not_called()


class CandidateBuildSBOMIntegrationTests(FirmwareSBOMFixture):
    def _build_status(self) -> dict:
        return {
            "ready": True,
            "tools": {
                "west": "/fixture/west",
                "cmake": "/fixture/cmake",
                "ninja": "/fixture/ninja",
                "arm_compiler": "/fixture/arm-zephyr-eabi-gcc",
            },
            "ncs": self.pre_ncs,
            "toolchain_container": {"declaration_matches": True},
        }

    def _materialized_source(self, suffix: str = "") -> Path:
        materialized = self.temporary / f"materialized{suffix}"
        materialized.mkdir()
        receipt_path = materialized / "ANTICIPY_SOURCE_RECEIPT.json"
        receipt_path.write_text(
            json.dumps(self.source_receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.assertEqual(sha256_file(receipt_path), self.source_receipt_sha256)
        return materialized

    def _run_build(
        self,
        return_code: int,
        *,
        reserved_directory: bool = False,
        artifact_symlink: bool = False,
        zephyr_symlink: bool = False,
        cache_overrides: dict[str, str] | None = None,
        cache_omissions: set[str] | None = None,
        extra_cache_lines: list[str] | None = None,
        mutate_snapshot_during_sbom: bool = False,
        suffix: str = "",
    ):
        flavor = (
            "-artifact-symlink"
            if artifact_symlink
            else "-zephyr-symlink" if zephyr_symlink else ""
        ) + suffix
        output = self.temporary / f"candidate-{return_code}{flavor}"
        materialized = self._materialized_source(flavor)
        snapshot = json.loads(json.dumps(self.pre_ncs))
        status = self._build_status()
        status["ncs"] = snapshot

        def fake_build(command, **kwargs):
            if return_code == 0:
                zephyr_output = output / "zephyr"
                if zephyr_symlink:
                    outside_directory = self.temporary / "outside-zephyr"
                    outside_directory.mkdir()
                    zephyr_output.parent.mkdir(parents=True)
                    zephyr_output.symlink_to(
                        outside_directory, target_is_directory=True
                    )
                else:
                    zephyr_output.mkdir(parents=True)
                for name, record in self.artifacts.items():
                    source = self.artifact_root / "zephyr" / name
                    destination = zephyr_output / name
                    if artifact_symlink and name == "zephyr.uf2":
                        outside = self.temporary / "outside-artifact.bin"
                        outside.write_bytes(b"outside bytes must never enter receipt")
                        destination.symlink_to(outside)
                    else:
                        shutil.copy2(source, destination)
                        self.assertEqual(destination.stat().st_size, record["bytes"])
                toolchain_prefix = self.toolchain["toolchain_container"][
                    "runtime_toolchain"
                ]["selected_prefix"]
                sdk = f"{toolchain_prefix}/opt/zephyr-sdk"
                arm_bin = f"{sdk}/arm-zephyr-eabi/bin"
                toolchain_python = (
                    f"{toolchain_prefix}/usr/local/bin/python3.8"
                )
                cache_entries = {
                    "BOARD": "STRING=xiao_ble_sense",
                    "BOARD_DIR": (
                        f"PATH={self.temporary / 'ncs' / 'zephyr' / 'boards' / 'arm' / 'xiao_ble'}"
                    ),
                    "CACHED_BOARD": "STRING=xiao_ble_sense",
                    "CACHED_CONF_FILE": (
                        "STRING=prj_xiao_ble_sense_devkitv2-adafruit.conf"
                    ),
                    "CMAKE_ASM_COMPILER": (
                        f"FILEPATH={arm_bin}/arm-zephyr-eabi-gcc"
                    ),
                    "CMAKE_COMMAND": (
                        f"INTERNAL={toolchain_prefix}/usr/local/bin/cmake"
                    ),
                    "CMAKE_CXX_COMPILER": (
                        f"STRING={arm_bin}/arm-zephyr-eabi-g++"
                    ),
                    "CMAKE_C_COMPILER": (
                        f"STRING={arm_bin}/arm-zephyr-eabi-gcc"
                    ),
                    "CMAKE_HOME_DIRECTORY": f"INTERNAL={materialized}",
                    "CMAKE_MAKE_PROGRAM": (
                        f"FILEPATH={toolchain_prefix}/usr/local/bin/ninja"
                    ),
                    "DTC_OVERLAY_FILE": (
                        "STRING=overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay"
                    ),
                    "WEST": f"INTERNAL={toolchain_python};-m;west",
                    "WEST_PYTHON": f"UNINITIALIZED={toolchain_python}",
                    "ZEPHYR_BASE": f"PATH={self.temporary / 'ncs' / 'zephyr'}",
                    "ZEPHYR_SDK_INSTALL_DIR": f"INTERNAL={sdk}",
                    "ZEPHYR_TOOLCHAIN_VARIANT": "INTERNAL=zephyr",
                    "Zephyr-sdk_DIR": f"PATH={sdk}/cmake",
                }
                cache_entries.update(cache_overrides or {})
                for key in cache_omissions or set():
                    cache_entries.pop(key, None)
                cache_lines = [
                    f"{key}:{value}" for key, value in sorted(cache_entries.items())
                ]
                cache_lines.extend(extra_cache_lines or [])
                cache = output / "CMakeCache.txt"
                cache.write_text("\n".join(cache_lines) + "\n", encoding="utf-8")
            else:
                output.mkdir(parents=True)
                if reserved_directory:
                    (output / sbom.SPDX_FILENAME).mkdir()
                else:
                    (output / sbom.SPDX_FILENAME).write_text(
                        "malicious build output\n", encoding="utf-8"
                    )
                (output / f".{sbom.SPDX_FILENAME}.tmp").write_text(
                    "malicious atomic temporary\n", encoding="utf-8"
                )
            return SimpleNamespace(returncode=return_code, stdout="fixture build log\n")

        def write_then_mutate_snapshot(path, document):
            record = sbom.write_validated_spdx(path, document)
            (output / "west-active-projects-frozen.tsv").write_text(
                f"nrf\t{'f' * 40}\n",
                encoding="utf-8",
            )
            return record

        with (
            mock.patch("build_candidate.ensure_materialized", return_value=self.source_receipt),
            mock.patch(
                "build_candidate.locked_source_date_epoch",
                return_value=SOURCE_DATE_EPOCH,
            ),
            mock.patch("build_candidate.tool_versions", return_value={"west": "fixture"}),
            mock.patch("build_candidate.subprocess.run", side_effect=fake_build),
            mock.patch(
                "build_candidate.write_validated_spdx",
                side_effect=(
                    write_then_mutate_snapshot
                    if mutate_snapshot_during_sbom
                    else sbom.write_validated_spdx
                ),
            ),
            mock.patch(
                "build_candidate.ncs_status",
                return_value=(True, json.loads(json.dumps(snapshot))),
            ),
        ):
            if return_code == 0:
                if (
                    artifact_symlink
                    or zephyr_symlink
                    or mutate_snapshot_during_sbom
                ):
                    with self.assertRaisesRegex(
                        RuntimeError, "candidate build or provenance"
                    ):
                        build(
                            FIRMWARE_ROOT / ".cache" / "fixture-source",
                            materialized,
                            self.temporary / "ncs",
                            output,
                            status,
                        )
                    return output, None
                return output, build(
                    FIRMWARE_ROOT / ".cache" / "fixture-source",
                    materialized,
                    self.temporary / "ncs",
                    output,
                    status,
                )
            expected_error = (
                "reserved SBOM output"
                if reserved_directory
                else "candidate build or provenance"
            )
            with self.assertRaisesRegex(RuntimeError, expected_error):
                build(
                    FIRMWARE_ROOT / ".cache" / "fixture-source",
                    materialized,
                    self.temporary / "ncs",
                    output,
                    status,
                )
            return output, None

    def test_success_emits_validated_sbom_cross_bound_in_receipt(self) -> None:
        output, receipt = self._run_build(0)
        path = output / sbom.SPDX_FILENAME
        self.assertTrue(receipt["candidate_accepted"])
        self.assertTrue(path.is_file())
        self.assertEqual(receipt["sbom"]["sha256"], sha256_file(path))
        self.assertEqual(receipt["sbom"]["path"], sbom.SPDX_FILENAME)
        self.assertEqual(receipt["sbom"]["generator"]["version"], "1.0.0")
        self.assertEqual(
            receipt["sbom"]["validator"]["jsonschema_version"], "4.26.0"
        )
        self.assertFalse(receipt["flash_approved"])
        self.assertFalse(receipt["flash_performed"])
        active_snapshot = output / "west-active-projects-frozen.tsv"
        self.assertEqual(
            active_snapshot.read_bytes(),
            (
                f"modules/sample\t{'a' * 40}\n"
                f"nrf\t{self.toolchain['nrf_connect_sdk']['commit']}\n"
                f"zephyr\t{self.toolchain['zephyr']['commit']}\n"
            ).encode("utf-8"),
        )
        self.assertEqual(
            receipt["toolchain"]["west_active_projects_frozen"],
            {
                "path": "west-active-projects-frozen.tsv",
                "sha256": sha256_file(active_snapshot),
                "project_count": 3,
            },
        )
        self.assertEqual(
            receipt["toolchain"]["nrf_west_yml_sha256"],
            self.toolchain["nrf_connect_sdk"]["west_manifest_sha256"],
        )
        self.assertEqual(
            receipt["toolchain"]["west_config_sha256"],
            "c" * 64,
        )
        for phase in ("pre_build_ncs", "post_build_ncs"):
            phase_evidence = receipt["toolchain"][phase]
            self.assertEqual(
                phase_evidence["active_projects_frozen_sha256"],
                sha256_file(active_snapshot),
            )
            self.assertEqual(
                phase_evidence["active_projects_frozen_project_count"], 3
            )
            self.assertEqual(
                phase_evidence["west_manifest_sha256"],
                self.toolchain["nrf_connect_sdk"]["west_manifest_sha256"],
            )
            self.assertEqual(phase_evidence["west_config_sha256"], "c" * 64)
        self.assertTrue(receipt["toolchain"]["cmake_inputs"]["verified"])
        cmake_inputs = receipt["toolchain"]["cmake_inputs"]
        self.assertEqual(len(cmake_inputs["observed_cache_entries"]), 17)
        self.assertEqual(
            cmake_inputs["expected"]["toolchain_prefix"],
            "/root/ncs/toolchains/7795df4459",
        )
        self.assertEqual(
            cmake_inputs["observed_cache_entries"]["BOARD"],
            {"type": "STRING", "value": "xiao_ble_sense"},
        )
        self.assertIn(
            f"-DZEPHYR_BASE:PATH={self.temporary / 'ncs' / 'zephyr'}",
            receipt["command"],
        )
        self.assertIn(
            "-DCONF_FILE:STRING=prj_xiao_ble_sense_devkitv2-adafruit.conf",
            receipt["command"],
        )
        self.assertIn(
            "-DDTC_OVERLAY_FILE:STRING="
            "overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay",
            receipt["command"],
        )

    def test_wrong_or_missing_locked_cmake_input_rejects_candidate(self) -> None:
        cases = (
            ("wrong-board", {"BOARD": "STRING=wrong_board"}, set()),
            (
                "wrong-board-directory",
                {"BOARD_DIR": f"PATH={self.temporary / 'other-board'}"},
                set(),
            ),
            (
                "escaped-config",
                {"CACHED_CONF_FILE": "STRING=../../wrong.conf"},
                set(),
            ),
            ("missing-overlay", {}, {"DTC_OVERLAY_FILE"}),
            (
                "wrong-toolchain-command",
                {"CMAKE_COMMAND": "INTERNAL=/tmp/untrusted/cmake"},
                set(),
            ),
            ("missing-west-python", {}, {"WEST_PYTHON"}),
        )
        for label, overrides, omissions in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    RuntimeError, "candidate build or provenance"
                ):
                    self._run_build(
                        0,
                        cache_overrides=overrides,
                        cache_omissions=omissions,
                        suffix=f"-{label}",
                    )

    def test_duplicate_required_cmake_cache_key_rejects_candidate(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "candidate build or provenance"):
            self._run_build(
                0,
                extra_cache_lines=["BOARD:STRING=xiao_ble_sense"],
                suffix="-duplicate-cache-key",
            )

    def test_board_alias_or_deprecation_remap_rejects_candidate(self) -> None:
        for key in ("BOARD_ALIAS", "BOARD_DEPRECATED"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(
                    RuntimeError, "candidate build or provenance"
                ):
                    self._run_build(
                        0,
                        extra_cache_lines=[f"{key}:STRING=xiao_ble_sense"],
                        suffix=f"-{key.lower()}",
                    )

    def test_failed_build_emits_no_sbom(self) -> None:
        output, _ = self._run_build(1)
        self.assertFalse((output / sbom.SPDX_FILENAME).exists())
        self.assertFalse((output / f".{sbom.SPDX_FILENAME}.tmp").exists())
        failure = json.loads(
            (output / "ANTICIPY_BUILD_FAILURE_RECEIPT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(failure["sbom"]["status"], "NOT_EMITTED")
        self.assertFalse(failure["candidate_accepted"])

    def test_snapshot_mutation_during_sbom_write_rejects_candidate(self) -> None:
        output, _ = self._run_build(
            0,
            mutate_snapshot_during_sbom=True,
            suffix="-snapshot-drift",
        )
        self.assertFalse((output / sbom.SPDX_FILENAME).exists())
        failure = json.loads(
            (output / "ANTICIPY_BUILD_FAILURE_RECEIPT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(failure["candidate_accepted"])
        self.assertIn(
            "snapshot bytes drifted",
            failure["sbom"]["detail"],
        )

    def test_failed_build_with_reserved_sbom_directory_is_refused(self) -> None:
        output, _ = self._run_build(1, reserved_directory=True)
        self.assertTrue((output / sbom.SPDX_FILENAME).is_dir())
        self.assertFalse((output / "ANTICIPY_BUILD_RECEIPT.json").exists())

    def test_artifact_symlinks_never_enter_failure_receipt(self) -> None:
        for label, arguments in (
            ("artifact", {"artifact_symlink": True}),
            ("zephyr-directory", {"zephyr_symlink": True}),
        ):
            with self.subTest(label=label):
                output, _ = self._run_build(0, **arguments)
                failure = json.loads(
                    (output / "ANTICIPY_BUILD_FAILURE_RECEIPT.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(failure["artifacts"], {})
                self.assertIn("traverse a symlink", failure["sbom"]["detail"])
                rendered = json.dumps(failure)
                self.assertNotIn(
                    hashlib.sha256(b"outside bytes must never enter receipt").hexdigest(),
                    rendered,
                )


if __name__ == "__main__":
    unittest.main()
