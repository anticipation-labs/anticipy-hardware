from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = FIRMWARE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_candidate import (  # noqa: E402
    canonical_active_projects_tsv,
    ensure_materialized,
    ncs_status,
    probe,
)
from materialize_replacement import (  # noqa: E402
    SOURCE_RECEIPT_NAME,
    apply_locked_patch,
    content_tree_sha256,
    deterministic_receipt,
    export_locked_source_tree,
    materialize,
)


UPSTREAM_CHECKOUT = FIRMWARE_ROOT / ".cache" / "omi-v2.0.1-Omi-firmware-v1.0"
REPLACEMENT_LOCK = FIRMWARE_ROOT / "replacement" / "replacement.lock.json"
TOOLCHAIN_LOCK = FIRMWARE_ROOT / "replacement" / "toolchain.lock.json"
UPSTREAM_FIXTURE = FIRMWARE_ROOT / "tests" / "fixtures" / "replacement_upstream"


def git_blob_oid(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def apply_patch_subset(
    destination: Path, patch: Path, included_paths: tuple[str, ...]
) -> None:
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=destination,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    command = [
        "git",
        "apply",
        "--whitespace=nowarn",
        *[f"--include={path}" for path in included_paths],
        str(patch),
    ]
    subprocess.run(
        command[:2] + ["--check"] + command[2:],
        cwd=destination,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        command,
        cwd=destination,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ReplacementLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.replacement = json.loads(REPLACEMENT_LOCK.read_text(encoding="utf-8"))
        self.toolchain = json.loads(TOOLCHAIN_LOCK.read_text(encoding="utf-8"))
        self.patch_path = FIRMWARE_ROOT / self.replacement["patch"]["path"]
        self.patch_text = self.patch_path.read_text(encoding="utf-8")

    def test_patch_hash_and_scope_are_locked(self) -> None:
        observed = hashlib.sha256(self.patch_path.read_bytes()).hexdigest()
        self.assertEqual(observed, self.replacement["patch"]["sha256"])
        changed_paths = {
            line.removeprefix("diff --git a/").split(" b/", 1)[0]
            for line in self.patch_text.splitlines()
            if line.startswith("diff --git a/")
        }
        self.assertEqual(
            changed_paths,
            {
                "CMakeLists.txt",
                "CMakePresets.json",
                "Kconfig",
                "README.rst",
                "build.sh",
                "client.py",
                "overlay/xiao_ble_sense_devkitv1-spisd.overlay",
                "overlay/xiao_ble_sense_devkitv1.overlay",
                "overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay",
                "prj_xiao_ble_sense_devkitv1-spisd.conf",
                "prj_xiao_ble_sense_devkitv1.conf",
                "prj_xiao_ble_sense_devkitv2-adafruit.conf",
                "src/battery_math.c",
                "src/battery_math.h",
                "src/battery_smoother.c",
                "src/battery_smoother.h",
                "src/button.c",
                "src/button.h",
                "src/codec.c",
                "src/codec.h",
                "src/led.c",
                "src/led.h",
                "src/lib/battery/battery.c",
                "src/main.c",
                "src/mic.c",
                "src/mic.h",
                "src/nfc.c",
                "src/nfc.h",
                "src/opus_packet_helpers.c",
                "src/sdcard.c",
                "src/sdcard.h",
                "src/speaker.c",
                "src/speaker.h",
                "src/storage.c",
                "src/storage.h",
                "src/transport.c",
                "src/transport.h",
                "src/transport_safety.c",
                "src/transport_safety.h",
                "src/utils.h",
            },
        )
        locked_critical = set(
            self.replacement["materialized_source"]["critical_file_sha256"]
        )
        deleted_paths = {
            "CMakePresets.json",
            "build.sh",
            "client.py",
            "overlay/xiao_ble_sense_devkitv1-spisd.overlay",
            "overlay/xiao_ble_sense_devkitv1.overlay",
            "prj_xiao_ble_sense_devkitv1-spisd.conf",
            "prj_xiao_ble_sense_devkitv1.conf",
            "src/button.c",
            "src/button.h",
            "src/nfc.c",
            "src/nfc.h",
            "src/sdcard.c",
            "src/sdcard.h",
            "src/speaker.c",
            "src/speaker.h",
            "src/storage.c",
            "src/storage.h",
        }
        self.assertEqual(
            locked_critical,
            (changed_paths - deleted_paths) | {"src/config.h"},
        )

    def test_patch_reduces_gatt_authority_to_encrypted_live_audio(self) -> None:
        added_lines = "\n".join(
            line
            for line in self.patch_text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ).lower()
        self.assertIn("bt_gatt_perm_read_encrypt", added_lines)
        self.assertIn("bt_gatt_perm_write_encrypt", added_lines)
        self.assertNotIn("dfu_service_uuid", added_lines)
        self.assertNotIn("storage_service", added_lines)
        self.assertNotIn("accel_service", added_lines)
        self.assertNotIn("gpregret", added_lines)
        self.assertNotIn("audio_characteristic_speaker_uuid", added_lines)

    def test_patch_contains_the_reviewed_live_stream_safety_repairs(self) -> None:
        self.assertIn("+CONFIG_OFFLINE_STORAGE=n", self.patch_text)
        self.assertIn("+CONFIG_BT_SMP_SC_PAIR_ONLY=y", self.patch_text)
        self.assertIn("+CONFIG_BT_BONDING_REQUIRED=y", self.patch_text)
        self.assertIn("+CONFIG_BT_SETTINGS=y", self.patch_text)
        self.assertIn("+CONFIG_SETTINGS_NVS=y", self.patch_text)
        self.assertIn("+CONFIG_FLASH_PAGE_LAYOUT=y", self.patch_text)
        self.assertIn("+CONFIG_I2S=n", self.patch_text)
        self.assertIn("+CONFIG_SPI=n", self.patch_text)
        self.assertIn("+CONFIG_USB_DEVICE_STACK=n", self.patch_text)
        self.assertIn("+#define AUDIO_VALUE_ATTRIBUTE_INDEX 2u", self.patch_text)
        self.assertIn("+    uint16_t att_mtu = bt_gatt_get_mtu(conn);", self.patch_text)
        self.assertIn("+        (void)k_sem_take(&tx_data_ready, K_FOREVER);", self.patch_text)
        self.assertIn("+        (void)k_sem_take(&codec_data_ready, K_FOREVER);", self.patch_text)
        self.assertIn("+    err = settings_load();", self.patch_text)
        self.assertIn("+    err = initialize_battery_service();", self.patch_text)
        self.assertIn(
            "+    ret = battery_scale_divider_millivolts(",
            self.patch_text,
        )
        self.assertIn(
            "+            nrfx_pdm_buffer_set(next_buffer, MIC_BUFFER_SAMPLES);",
            self.patch_text,
        )
        for deleted in (
            "CMakePresets.json",
            "build.sh",
            "client.py",
            "overlay/xiao_ble_sense_devkitv1-spisd.overlay",
            "overlay/xiao_ble_sense_devkitv1.overlay",
            "prj_xiao_ble_sense_devkitv1-spisd.conf",
            "prj_xiao_ble_sense_devkitv1.conf",
            "src/button.c",
            "src/button.h",
            "src/nfc.c",
            "src/nfc.h",
            "src/sdcard.c",
            "src/sdcard.h",
            "src/speaker.c",
            "src/speaker.h",
            "src/storage.c",
            "src/storage.h",
        ):
            self.assertIn(f"diff --git a/{deleted} b/{deleted}", self.patch_text)

    def test_patch_contains_isr_codec_indicator_and_legacy_surface_guards(
        self,
    ) -> None:
        added_lines = "\n".join(
            line
            for line in self.patch_text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        self.assertIn("IRQ_CONNECT(", added_lines)
        self.assertIn("nrfx_isr, nrfx_pdm_irq_handler", added_lines)
        self.assertNotIn("IRQ_DIRECT_CONNECT", added_lines)
        self.assertIn("nrfx_pdm_enable_check()", added_lines)
        self.assertIn("k_sem_take(&pdm_stopped", added_lines)
        self.assertIn("atomic_get(&hardware_started)", added_lines)
        self.assertNotIn("pdm_fault_work", added_lines)
        self.assertIn("OPUS_RESET_STATE", added_lines)
        self.assertIn("set_codec_error_callback", added_lines)
        self.assertIn("if (output_size < 0)", added_lines)
        self.assertIn("mic_emergency_power_off()", added_lines)
        self.assertIn("k_panic()", added_lines)
        self.assertIn("BT_GATT_CCC_MANAGED(", added_lines)
        self.assertIn("fresh_audio_ccc_authorized", added_lines)
        self.assertIn("fresh_audio_ccc_connection", added_lines)
        self.assertIn("ADVERTISING_RESTART_RETRY_LIMIT", added_lines)
        self.assertIn("ADVERTISING_RECOVERY_DELAY_MS", added_lines)
        self.assertIn("BT_HCI_ERR_REMOTE_USER_TERM_CONN", added_lines)
        self.assertNotIn("/Volumes/XIAO-SENSE", added_lines)
        self.assertNotIn("friend.based.com", added_lines)
        self.assertNotIn("ABC123", added_lines)
        self.assertNotIn("CONFIG_OFFLINE_STORAGE=y", added_lines)

    def test_behavior_contract_keeps_existing_audio_protocol(self) -> None:
        behavior = self.replacement["behavior_contract"]
        self.assertEqual(behavior["advertised_complete_name"], "Anticipy")
        self.assertEqual(
            behavior["audio_service_uuid"], "19B10000-E8F2-537E-4F6C-D104768A1214"
        )
        self.assertEqual(
            behavior["audio_data_uuid"], "19B10001-E8F2-537E-4F6C-D104768A1214"
        )
        self.assertEqual(
            behavior["audio_codec_uuid"], "19B10002-E8F2-537E-4F6C-D104768A1214"
        )
        self.assertEqual(behavior["codec_id"], 20)
        self.assertEqual(behavior["battery_first_notification_delay_ms"], 0)
        self.assertEqual(behavior["battery_notification_interval_ms"], 15_000)
        self.assertEqual(behavior["battery_smoothing"]["previous_weight"], 3)
        self.assertEqual(behavior["battery_smoothing"]["sample_weight"], 1)
        self.assertTrue(behavior["audio_gatt_encryption_required"])
        self.assertTrue(behavior["bond_persistence_configured"])
        self.assertFalse(behavior["offline_storage_enabled"])
        self.assertFalse(behavior["legacy_dfu_service_enabled"])
        self.assertTrue(behavior["capture_requires_audio_ccc_subscription"])
        self.assertTrue(
            behavior["capture_requires_fresh_per_connection_ccc_write"]
        )
        self.assertTrue(behavior["battery_percentage_is_uncalibrated_estimate"])
        self.assertTrue(
            behavior["runtime_battery_measurement_failure_disconnects"]
        )
        self.assertFalse(behavior["firmware_revision_advertised"])
        self.assertTrue(behavior["advertising_restart_enabled"])
        self.assertTrue(
            behavior["initial_advertising_failure_recovery_enabled"]
        )
        self.assertFalse(self.replacement["explicit_non_claims"]["artifact_built"])
        self.assertFalse(self.replacement["explicit_non_claims"]["flash_performed"])
        self.assertFalse(self.replacement["explicit_non_claims"]["haptic_support_added"])
        self.assertFalse(self.replacement["explicit_non_claims"]["owner_authenticated"])
        self.assertFalse(
            self.replacement["explicit_non_claims"][
                "physical_enrollment_gesture_added"
            ]
        )
        self.assertFalse(
            self.replacement["explicit_non_claims"]["bond_erase_gesture_added"]
        )

    def test_toolchain_uses_immutable_commits_and_container_digest(self) -> None:
        self.assertRegex(self.toolchain["nrf_connect_sdk"]["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(self.toolchain["zephyr"]["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(
            self.toolchain["toolchain_container"]["digest"], r"^sha256:[0-9a-f]{64}$"
        )
        runtime = self.toolchain["toolchain_container"]["runtime_toolchain"]
        self.assertEqual(runtime["bundle_id"], "7795df4459")
        self.assertEqual(runtime["ncs_version"], "v2.5.0")
        self.assertEqual(
            runtime["metadata_sha256"],
            "0f439f881430912d9d57ab84c7f76501222a93805affc2e914be479055045a81",
        )
        self.assertEqual(
            runtime["selected_prefix"], "/root/ncs/toolchains/7795df4459"
        )
        self.assertEqual(self.toolchain["nrf_connect_sdk"]["tag"], "v2.5.0")
        self.assertEqual(self.toolchain["zephyr"]["tag"], "v3.4.99-ncs1")
        self.assertEqual(self.toolchain["candidate_build"]["board"], "xiao_ble_sense")
        self.assertEqual(
            self.toolchain["candidate_build"]["board_definition"]["zephyr_path"],
            "boards/arm/xiao_ble",
        )
        self.assertRegex(
            self.toolchain["candidate_build"]["board_definition"]["git_tree_oid"],
            r"^[0-9a-f]{40}$",
        )
        self.assertFalse(self.toolchain["flash_approved"])

    def test_receipt_requirements_bind_active_and_declared_project_evidence(self) -> None:
        requirements = self.toolchain["receipt_requirements"]
        self.assertTrue(
            any("active west project snapshot" in item for item in requirements)
        )
        self.assertTrue(
            any(
                "credential-free HTTPS repositories" in item
                and "clean status before and after build" in item
                for item in requirements
            )
        )
        self.assertTrue(
            any(
                "declared, active, and inactive west project inventory and counts"
                in item
                for item in requirements
            )
        )
        self.assertTrue(
            any(
                "nrf/west.yml and .west/config" in item
                and "pre-build and post-build sha256" in item
                for item in requirements
            )
        )
        obsolete = "\n".join(requirements).lower()
        self.assertNotIn("manifest --freeze", obsolete)
        self.assertNotIn("all west project commits", obsolete)

    def test_materialized_cmake_leaves_board_selection_to_the_lock(self) -> None:
        self.assertIn("-set(BOARD seeed_xiao_nrf52840_sense)", self.patch_text)
        self.assertNotIn("+set(BOARD", self.patch_text)

    def test_build_probe_never_claims_an_artifact_or_flash(self) -> None:
        status = probe(
            UPSTREAM_CHECKOUT,
            FIRMWARE_ROOT / ".build" / "ncs-v2.5.0",
        )
        self.assertEqual(status["status"], "PINNED_CANDIDATE_BUILD_ENVIRONMENT_ONLY")
        self.assertFalse(status["artifact_built"])
        self.assertFalse(status["flash_approved"])
        self.assertFalse(status["flash_performed"])
        self.assertRegex(
            status["toolchain_container"]["expected_digest"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertEqual(
            status["toolchain_container"]["provenance"],
            "UNVERIFIED_OPERATOR_DECLARATION",
        )
        self.assertNotIn("attested", status["toolchain_container"])

    def test_tree_hash_includes_modes_directories_and_nested_receipt_names(self) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=FIRMWARE_ROOT / ".build") as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            source = nested / "source.c"
            source.write_text("int value;\n", encoding="utf-8")
            nested_receipt = nested / SOURCE_RECEIPT_NAME
            nested_receipt.write_text("one\n", encoding="utf-8")
            baseline = content_tree_sha256(root)

            nested_receipt.write_text("two\n", encoding="utf-8")
            self.assertNotEqual(content_tree_sha256(root), baseline)
            nested_receipt.write_text("one\n", encoding="utf-8")
            source.chmod(0o755)
            self.assertNotEqual(content_tree_sha256(root), baseline)
            source.chmod(0o644)
            (root / SOURCE_RECEIPT_NAME).write_text("ignored root receipt\n")
            self.assertEqual(content_tree_sha256(root), baseline)

    def test_existing_receipt_requires_the_locked_byte_hash(self) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=FIRMWARE_ROOT / ".build") as directory:
            destination = Path(directory)
            observed = self.replacement["materialized_source"][
                "critical_file_sha256"
            ]
            receipt = deterministic_receipt(self.replacement, observed)
            receipt_path = destination / SOURCE_RECEIPT_NAME
            receipt_path.write_text(
                json.dumps(receipt, indent=4, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                json.loads(receipt_path.read_text(encoding="utf-8")), receipt
            )
            self.assertNotEqual(
                hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                self.replacement["materialized_source"]["source_receipt_sha256"],
            )
            with mock.patch(
                "build_candidate.verify_materialized", return_value=observed
            ):
                with self.assertRaisesRegex(RuntimeError, "receipt hash is drifted"):
                    ensure_materialized(UPSTREAM_CHECKOUT, destination)


class NCSWorkspaceProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        self.temporary = Path(
            tempfile.mkdtemp(prefix="ncs-status-test-", dir=FIRMWARE_ROOT / ".build")
        )
        self.workspace = self.temporary / "workspace"
        self.workspace.mkdir()
        (self.workspace / ".west").mkdir()
        (self.workspace / ".west" / "config").write_text(
            "[manifest]\npath = nrf\nfile = west.yml\n", encoding="utf-8"
        )
        self.nrf_commit = self._init_repo(
            self.workspace / "nrf", {"west.yml": "manifest:\n  projects: []\n"}
        )
        board_files = {
            "boards/arm/xiao_ble/xiao_ble_sense.yaml": "identifier: xiao_ble_sense\n",
            "boards/arm/xiao_ble/xiao_ble_sense_defconfig": "CONFIG_BUILD_OUTPUT_UF2=y\n",
            "boards/arm/xiao_ble/xiao_ble_sense.dts": "/dts-v1/;\n",
            "boards/arm/xiao_ble/Kconfig.board": "config BOARD_XIAO_BLE\n",
            "boards/arm/xiao_ble/board.cmake": "board_runner_args(jlink --device=nRF52840_xxAA)\n",
        }
        self.zephyr_commit = self._init_repo(
            self.workspace / "zephyr", {"VERSION": "3.4.99\n", **board_files}
        )
        self._init_repo(self.workspace / "modules" / "sample", {"sample.c": "int x;\n"})
        self.west_lines = self.workspace / "west-active-lines.json"
        self.west_lines.write_text(
            json.dumps(
                [
                    [
                        "zephyr",
                        str(self.workspace / "zephyr"),
                        "https://github.com/nrfconnect/sdk-zephyr.git",
                    ],
                    [
                        "modules/sample",
                        str(self.workspace / "modules" / "sample"),
                        "https://example.invalid/sample.git",
                    ],
                ]
            ),
            encoding="utf-8",
        )
        self.west_command_log = self.workspace / "west-command.log"
        self.fake_west = self.workspace / "fake-west"
        self.fake_west.write_text(
            f"""#!/usr/bin/env python3
import json
import sys
from pathlib import Path
root = Path({str(self.workspace)!r})
lines_path = Path({str(self.west_lines)!r})
log_path = Path({str(self.west_command_log)!r})
args = sys.argv[1:]
with log_path.open("a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\\n")
if args == ["topdir"]:
    print(root)
elif args[:2] == ["list", "-f"]:
    for path, absolute, repository in json.loads(lines_path.read_text(encoding="utf-8")):
        print(f"{{path}}\\t{{absolute}}\\t{{repository}}")
elif args == ["--version"]:
    print("West version: test")
else:
    raise SystemExit(2)
""",
            encoding="utf-8",
        )
        self.fake_west.chmod(0o755)
        self.toolchain = json.loads(TOOLCHAIN_LOCK.read_text(encoding="utf-8"))
        self.toolchain["nrf_connect_sdk"]["commit"] = self.nrf_commit
        self.toolchain["nrf_connect_sdk"]["west_manifest_sha256"] = hashlib.sha256(
            (self.workspace / "nrf" / "west.yml").read_bytes()
        ).hexdigest()
        self.toolchain["zephyr"]["commit"] = self.zephyr_commit
        board_root = self.workspace / "zephyr" / "boards" / "arm" / "xiao_ble"
        self.toolchain["candidate_build"]["board_definition"]["git_tree_oid"] = (
            subprocess.run(
                ["git", "rev-parse", "HEAD:boards/arm/xiao_ble"],
                cwd=self.workspace / "zephyr",
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
        )
        self.toolchain["candidate_build"]["board_definition"][
            "critical_file_sha256"
        ] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in board_root.iterdir()
            if path.is_file()
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.temporary, ignore_errors=True)

    def _set_west_lines(self, lines: list[list[str]]) -> None:
        self.west_lines.write_text(json.dumps(lines), encoding="utf-8")

    @staticmethod
    def _init_repo(path: Path, files: dict[str, str]) -> str:
        path.mkdir(parents=True)
        subprocess.run(["git", "init", "--quiet"], cwd=path, check=True)
        for relative, content in files.items():
            target = path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=path, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Anticipy Test",
                "-c",
                "user.email=test@invalid.example",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            cwd=path,
            check=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def test_clean_workspace_binds_only_active_projects_in_canonical_snapshot(self) -> None:
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertTrue(ok, detail["detail"])
        self.assertEqual(detail["project_count"], 3)
        self.assertEqual(set(detail["project_commits"]), {"nrf", "zephyr", "modules/sample"})
        self.assertRegex(detail["project_commits_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(
            detail["active_projects_frozen_sha256"], r"^[0-9a-f]{64}$"
        )
        self.assertEqual(detail["active_projects_frozen_project_count"], 3)
        self.assertEqual(
            detail["active_projects_frozen_filename"],
            "west-active-projects-frozen.tsv",
        )
        self.assertEqual(
            list(detail["project_commits"]),
            ["modules/sample", "nrf", "zephyr"],
        )
        commands = self.west_command_log.read_text(encoding="utf-8")
        self.assertNotIn("manifest", commands)
        self.assertNotIn("--freeze", commands)
        self.assertEqual(
            detail["board_definition_git_tree_oid"],
            self.toolchain["candidate_build"]["board_definition"]["git_tree_oid"],
        )
        self.assertEqual(
            detail["board_definition_file_sha256"],
            self.toolchain["candidate_build"]["board_definition"][
                "critical_file_sha256"
            ],
        )

    def test_snapshot_bytes_are_utf8_sorted_and_include_nrf(self) -> None:
        content = canonical_active_projects_tsv(
            {
                "zephyr": "c" * 40,
                "nrf": "b" * 40,
                "modules/sample": "a" * 40,
            }
        )
        self.assertEqual(
            content,
            (
                "modules/sample\t" + "a" * 40 + "\n"
                "nrf\t" + "b" * 40 + "\n"
                "zephyr\t" + "c" * 40 + "\n"
            ).encode("utf-8"),
        )

    def test_inaccessible_inactive_project_is_never_listed_or_inspected(self) -> None:
        inaccessible = self.workspace / "modules" / "private-inactive"
        self.assertFalse(inaccessible.exists())
        real_head = sys.modules["build_candidate"].repository_head

        def guarded_head(path: Path) -> str:
            if "private-inactive" in path.parts:
                raise AssertionError("inactive project must not be inspected")
            return real_head(path)

        with mock.patch("build_candidate.repository_head", side_effect=guarded_head):
            ok, detail = ncs_status(
                self.workspace, self.toolchain, str(self.fake_west)
            )
        self.assertTrue(ok, detail["detail"])
        self.assertNotIn("private-inactive", detail["project_commits"])
        commands = [
            json.loads(line)
            for line in self.west_command_log.read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(all("--all" not in command for command in commands))
        self.assertTrue(all("--freeze" not in command for command in commands))

    def test_untrusted_manifest_or_config_fails_before_active_discovery(self) -> None:
        manifest = self.workspace / "nrf" / "west.yml"
        manifest.write_text(
            "manifest:\n  projects:\n    - name: private-inactive\n",
            encoding="utf-8",
        )
        with mock.patch(
            "build_candidate.active_west_projects",
            side_effect=AssertionError("must fail before active discovery"),
        ):
            ok, detail = ncs_status(
                self.workspace, self.toolchain, str(self.fake_west)
            )
        self.assertFalse(ok)
        self.assertIn("dirty west project: nrf", detail["detail"])
        subprocess.run(["git", "restore", "west.yml"], cwd=manifest.parent, check=True)

        (self.workspace / ".west" / "config").write_text(
            "[manifest]\npath = changed\nfile = west.yml\n",
            encoding="utf-8",
        )
        with mock.patch(
            "build_candidate.active_west_projects",
            side_effect=AssertionError("must fail before active discovery"),
        ):
            ok, detail = ncs_status(
                self.workspace, self.toolchain, str(self.fake_west)
            )
        self.assertFalse(ok)
        self.assertIn(".west manifest must be exactly nrf/west.yml", detail["detail"])

    def test_west_manifest_project_row_is_bound_once_when_listed(self) -> None:
        current = json.loads(self.west_lines.read_text(encoding="utf-8"))
        current.append(
            [
                "nrf",
                str(self.workspace / "nrf"),
                "",
            ]
        )
        self._set_west_lines(current)
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertTrue(ok, detail["detail"])
        self.assertEqual(list(detail["project_commits"]).count("nrf"), 1)
        self.assertEqual(
            detail["project_repositories"]["nrf"],
            self.toolchain["nrf_connect_sdk"]["repository"],
        )

    def test_duplicate_unsafe_and_credentialed_active_entries_fail_closed(self) -> None:
        valid_sample = [
            "modules/sample",
            str(self.workspace / "modules" / "sample"),
            "https://example.invalid/sample.git",
        ]
        cases = (
            ("duplicate", [valid_sample, valid_sample], "duplicate path"),
            (
                "parent traversal",
                [
                    [
                        "../sample",
                        str(self.workspace.parent / "sample"),
                        "https://example.invalid/sample.git",
                    ]
                ],
                "relative, normalized, and safe",
            ),
            (
                "west metadata",
                [
                    [
                        ".west/private",
                        str(self.workspace / ".west" / "private"),
                        "https://example.invalid/private.git",
                    ]
                ],
                "relative, normalized, and safe",
            ),
            (
                "credential",
                [
                    [
                        "modules/sample",
                        str(self.workspace / "modules" / "sample"),
                        "https://user:secret@example.invalid/sample.git",
                    ]
                ],
                "credential-free",
            ),
            (
                "repository whitespace",
                [
                    [
                        "modules/sample",
                        str(self.workspace / "modules" / "sample"),
                        "https://example.invalid/sample repo.git",
                    ]
                ],
                "printable URL",
            ),
        )
        for label, lines, message in cases:
            with self.subTest(label=label):
                self._set_west_lines(lines)
                ok, detail = ncs_status(
                    self.workspace, self.toolchain, str(self.fake_west)
                )
                self.assertFalse(ok)
                self.assertIn(message, detail["detail"])

    def test_malformed_or_drifted_active_head_fails_closed(self) -> None:
        with mock.patch(
            "build_candidate.repository_head",
            return_value="A" * 40,
        ):
            ok, detail = ncs_status(
                self.workspace, self.toolchain, str(self.fake_west)
            )
        self.assertFalse(ok)
        self.assertIn("40-character lowercase hexadecimal", detail["detail"])

        self._set_west_lines(
            [
                [
                    "zephyr",
                    str(self.workspace / "zephyr"),
                    "https://github.com/nrfconnect/sdk-zephyr.git",
                ]
            ]
        )
        drifted = dict(self.toolchain)
        drifted["zephyr"] = dict(self.toolchain["zephyr"])
        drifted["zephyr"]["commit"] = "f" * 40
        ok, detail = ncs_status(self.workspace, drifted, str(self.fake_west))
        self.assertFalse(ok)
        self.assertIn("Zephyr commit mismatch", detail["detail"])

    def test_missing_or_drifted_locked_board_definition_fails_closed(self) -> None:
        board = self.workspace / "zephyr" / "boards" / "arm" / "xiao_ble"
        (board / "xiao_ble_sense.yaml").write_text(
            "identifier: wrong_board\n", encoding="utf-8"
        )
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertFalse(ok)
        self.assertIn("dirty west project: zephyr", detail["detail"])
        self.assertIn("locked board definition file mismatch", detail["detail"])

    def test_dirty_dependency_and_changed_west_config_fail_closed(self) -> None:
        dirty = self.workspace / "modules" / "sample" / "untracked.c"
        dirty.write_text("int dirty;\n", encoding="utf-8")
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertFalse(ok)
        self.assertIn("dirty west project: modules/sample", detail["detail"])
        dirty.unlink()

        tracked = self.workspace / "modules" / "sample" / "sample.c"
        tracked.write_text("int changed;\n", encoding="utf-8")
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertFalse(ok)
        self.assertIn("dirty west project: modules/sample", detail["detail"])
        subprocess.run(
            ["git", "restore", "sample.c"],
            cwd=tracked.parent,
            check=True,
        )

        (self.workspace / ".west" / "config").write_text(
            "[manifest]\npath = changed\nfile = west.yml\n", encoding="utf-8"
        )
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertFalse(ok)
        self.assertIn(".west manifest must be exactly nrf/west.yml", detail["detail"])

    def test_non_repository_project_cannot_resolve_to_an_outer_repository(self) -> None:
        project = self.workspace / "modules" / "sample"
        shutil.rmtree(project / ".git")
        ok, detail = ncs_status(self.workspace, self.toolchain, str(self.fake_west))
        self.assertFalse(ok)
        self.assertIn("west project is not a Git worktree root", detail["detail"])


class ReplacementPatchFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        cls.temporary = Path(
            tempfile.mkdtemp(prefix="replacement-fixture-", dir=FIRMWARE_ROOT / ".build")
        )
        cls.source = cls.temporary / "source"
        shutil.copytree(UPSTREAM_FIXTURE, cls.source)
        cls.upstream = json.loads(
            (FIRMWARE_ROOT / "upstream.lock.json").read_text(encoding="utf-8")
        )
        cls.pre_patch_blob_oids = {
            relative: git_blob_oid(cls.source / fixture_relative)
            for relative, fixture_relative in {
                "Friend/firmware/firmware_v1.0/CMakeLists.txt": "CMakeLists.txt",
                "Friend/firmware/firmware_v1.0/prj_xiao_ble_sense_devkitv2-adafruit.conf": "prj_xiao_ble_sense_devkitv2-adafruit.conf",
                "Friend/firmware/firmware_v1.0/src/config.h": "src/config.h",
                "Friend/firmware/firmware_v1.0/src/transport.c": "src/transport.c",
            }.items()
        }
        cls.replacement = json.loads(REPLACEMENT_LOCK.read_text(encoding="utf-8"))
        cls.patch_path = FIRMWARE_ROOT / cls.replacement["patch"]["path"]
        apply_patch_subset(
            cls.source,
            cls.patch_path,
            (
                "CMakeLists.txt",
                "prj_xiao_ble_sense_devkitv2-adafruit.conf",
                "src/battery_math.c",
                "src/battery_math.h",
                "src/battery_smoother.c",
                "src/battery_smoother.h",
                "src/transport.c",
                "src/transport_safety.c",
                "src/transport_safety.h",
            ),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temporary, ignore_errors=True)

    def test_committed_fixture_is_the_exact_locked_upstream_preimage(self) -> None:
        for relative, observed in self.pre_patch_blob_oids.items():
            self.assertEqual(observed, self.upstream["audited_blobs"][relative])

    def test_name_protocol_and_battery_interval_do_not_drift(self) -> None:
        config = (self.source / "prj_xiao_ble_sense_devkitv2-adafruit.conf").read_text(
            encoding="utf-8"
        )
        transport = (self.source / "src" / "transport.c").read_text(encoding="utf-8")
        codec_config = (self.source / "src" / "config.h").read_text(encoding="utf-8")

        self.assertIn('CONFIG_BT_DEVICE_NAME="Anticipy"', config)
        self.assertIn('CONFIG_BT_DIS_MODEL="Anticipy Pendant"', config)
        self.assertIn("BT_DATA_NAME_COMPLETE", transport)
        self.assertIn("sizeof(CONFIG_BT_DEVICE_NAME) - 1u", transport)
        for uuid_prefix in ("0x19B10000", "0x19B10001", "0x19B10002"):
            self.assertIn(uuid_prefix, transport)
        self.assertIn("0xD104768A1214", transport)
        self.assertIn("#define CODEC_ID 20", codec_config)
        self.assertIn("#define BATTERY_REFRESH_INTERVAL 15000", transport)
        self.assertIn("bt_bas_set_battery_level(battery_percentage)", transport)
        self.assertIn("&battery_work, K_NO_WAIT", transport)
        self.assertIn("K_MSEC(BATTERY_REFRESH_INTERVAL)", transport)
        self.assertIn("k_work_cancel_delayable(&battery_work)", transport)
        self.assertNotIn("k_work_cancel_delayable_sync", transport)
        startup = transport[transport.index("int transport_start(void)") :]
        self.assertLess(
            startup.index("initialize_battery_service()"),
            startup.index("bt_le_adv_start("),
        )
        self.assertLess(
            transport.index("bt_bas_set_battery_level(battery_percentage)"),
            transport.index("int transport_start(void)"),
        )

    def test_selected_config_and_codec_surface_are_fail_closed(self) -> None:
        config = (self.source / "prj_xiao_ble_sense_devkitv2-adafruit.conf").read_text(
            encoding="utf-8"
        )
        cmake = (self.source / "CMakeLists.txt").read_text(encoding="utf-8")
        for required in (
            "CONFIG_OFFLINE_STORAGE=n",
            "CONFIG_DISK_ACCESS=n",
            "CONFIG_FILE_SYSTEM=n",
            "CONFIG_I2C=n",
            "CONFIG_SENSOR=n",
            "CONFIG_I2S=n",
            "CONFIG_SPI=n",
            "CONFIG_BT_SMP=y",
            "CONFIG_BT_SMP_SC_PAIR_ONLY=y",
            "CONFIG_BT_BONDING_REQUIRED=y",
            "CONFIG_BT_SETTINGS=y",
            "CONFIG_SETTINGS=y",
            "CONFIG_SETTINGS_NVS=y",
            "CONFIG_FLASH_PAGE_LAYOUT=y",
            "CONFIG_NVS=y",
            "CONFIG_BT_DIS_FW_REV=n",
        ):
            self.assertIn(required, config)
        self.assertNotIn("CONFIG_BT_DIS_FW_REV_STR=", config)
        self.assertIn("CONFIG_USB_DEVICE_STACK=n", config)
        self.assertIn("CONFIG_USB_CDC_ACM=n", config)
        self.assertNotIn("CONFIG_USB_DEVICE_STACK=y", config)
        for required in (
            "src/battery_math.c",
            "src/opus_packet_helpers.c",
            "src/transport_safety.c",
            "src/lib/opus-1.2.1/biquad_alt.c",
            "src/lib/opus-1.2.1/lin2log.c",
            "src/lib/opus-1.2.1/log2lin.c",
            "-Werror=stringop-overread",
            "-Werror=use-after-free=2",
        ):
            self.assertIn(required, cmake)
        for dormant in (
            "src/lib/opus-1.2.1/encode_frame_FIX.c",
            "src/lib/opus-1.2.1/NSQ.c",
            "src/lib/opus-1.2.1/NSQ_del_dec.c",
            "src/lib/opus-1.2.1/opus_decoder.c",
            "src/lib/opus-1.2.1/opus_multistream_decoder.c",
            "src/button.c",
            "src/sdcard.c",
            "src/speaker.c",
            "src/storage.c",
        ):
            self.assertNotIn(dormant, cmake)

    def test_transport_is_encrypted_ccc_gated_live_audio_only(self) -> None:
        transport = (self.source / "src" / "transport.c").read_text(encoding="utf-8")
        self.assertIn("BT_GATT_PERM_READ_ENCRYPT", transport)
        self.assertIn("BT_GATT_PERM_WRITE_ENCRYPT", transport)
        self.assertIn("BT_GATT_CCC_MANAGED(", transport)
        self.assertIn("audio_ccc_authorize_write", transport)
        self.assertIn("audio_ccc_authorized_match", transport)
        self.assertIn("fresh_audio_ccc_authorized", transport)
        self.assertIn("#define AUDIO_VALUE_ATTRIBUTE_INDEX 2u", transport)
        self.assertIn("static struct bt_conn *acquire_current_connection(void)", transport)
        self.assertIn("conn = bt_conn_ref(conn);", transport)
        self.assertIn("bt_gatt_is_subscribed(", transport)
        self.assertIn("request_audio_state(true, 0)", transport)
        self.assertIn("request_audio_state(false, 0)", transport)
        self.assertNotIn("storage_service", transport)
        self.assertNotIn("dfu_service", transport)
        self.assertNotIn("accel_service", transport)
        self.assertNotIn("current_mtu", transport)
        self.assertNotIn("k_yield", transport)

        ccc_body = transport[
            transport.rindex("static void audio_ccc_config_changed_handler(") :
        ]
        ccc_body = ccc_body[
            ccc_body.index("{") :
            ccc_body.index("static struct battery_smoother")
        ]
        self.assertNotIn("mic_start(", ccc_body)
        self.assertNotIn("mic_stop(", ccc_body)

    def test_transport_startup_consent_reconnect_and_queue_contracts(self) -> None:
        transport = (self.source / "src" / "transport.c").read_text(encoding="utf-8")

        startup = transport[transport.index("int transport_start(void)") :]
        self.assertLess(
            startup.index("bt_gatt_service_register(&audio_service)"),
            startup.index("bt_enable(NULL)"),
        )
        self.assertLess(
            startup.index("bt_enable(NULL)"),
            startup.index("settings_load()"),
        )
        self.assertLess(
            startup.index("settings_load()"),
            startup.index("initialize_battery_service()"),
        )
        self.assertLess(
            startup.index("initialize_battery_service()"),
            startup.index("bt_le_adv_start("),
        )
        self.assertLess(
            startup.index("atomic_set(&transport_ready, 1)"),
            startup.index("bt_le_adv_start("),
        )
        self.assertIn(
            "Initial advertising failed; recovery scheduled",
            startup,
        )
        self.assertIn(
            "k_work_reschedule(\n"
            "            &advertising_restart_work,\n"
            "            K_MSEC(ADVERTISING_RESTART_DELAY_MS))",
            startup,
        )
        self.assertNotIn("atomic_clear(&transport_ready)", startup)

        connected = transport[
            transport.index("static void transport_connected(") :
            transport.index("static void transport_disconnected(")
        ]
        self.assertLess(
            connected.index("current_connection = new_connection"),
            connected.index("bt_conn_get_info("),
        )
        self.assertIn(
            "atomic_clear(&fresh_audio_ccc_authorized)", connected
        )
        self.assertIn(
            "&battery_work, K_NO_WAIT", connected
        )

        disconnected = transport[
            transport.index("static void transport_disconnected(") :
            transport.index("static bool le_param_req(")
        ]
        self.assertIn(
            "atomic_clear(&fresh_audio_ccc_authorized)", disconnected
        )
        self.assertIn(
            "k_work_reschedule(\n"
            "            &advertising_restart_work, K_NO_WAIT)",
            disconnected,
        )

        restart = transport[
            transport.index("static void restart_advertising(") :
            transport.index("static uint8_t tx_queue[")
        ]
        self.assertIn("ADVERTISING_RESTART_RETRY_LIMIT", restart)
        self.assertIn("ADVERTISING_RECOVERY_DELAY_MS", restart)
        self.assertIn("err == 0 || err == -EALREADY", restart)
        self.assertGreaterEqual(restart.count("k_work_reschedule("), 2)

        self.assertIn(
            "(void)k_sem_take(&audio_control_event, K_FOREVER)",
            transport,
        )
        self.assertIn(
            "(void)k_sem_take(&tx_data_ready, K_FOREVER)",
            transport,
        )
        self.assertIn("bt_gatt_get_mtu(conn)", transport)
        self.assertIn("AUDIO_NOTIFY_RETRY_LIMIT", transport)
        self.assertIn("transport_fragment_commit(", transport)
        self.assertNotIn("info.le.data_len->tx_max_len - 7", transport)

        consent_write = transport[
            transport.rindex("static ssize_t audio_ccc_authorize_write(") :
            transport.rindex("static bool audio_ccc_authorized_match(")
        ]
        self.assertIn("bind_fresh_audio_authorization(conn)", consent_write)
        self.assertIn(
            "bt_gatt_is_subscribed(", consent_write
        )
        self.assertIn("request_audio_state(false", consent_write)

        consent_changed = transport[
            transport.rindex("static void audio_ccc_config_changed_handler(") :
            transport.index("static struct battery_smoother")
        ]
        self.assertIn(
            "connection_has_fresh_audio_authorization",
            consent_changed,
        )
        self.assertIn("request_audio_state(false, -EACCES)", consent_changed)

        authorization = transport[
            transport.index(
                "static bool connection_has_fresh_audio_authorization("
            ) :
            transport.index("static void restart_advertising(")
        ]
        self.assertIn("current_connection == conn", authorization)
        self.assertIn("fresh_audio_ccc_connection == conn", authorization)
        self.assertIn("bt_gatt_is_subscribed(", authorization)

        start_pipeline = transport[
            transport.index("static int start_audio_pipeline(") :
            transport.index("bool transport_audio_is_active(")
        ]
        self.assertLess(
            start_pipeline.index("audio_capture_authorized("),
            start_pipeline.index("mic_start()"),
        )

        audio_control = transport[
            transport.index("static void audio_control(") :
            transport.index("void transport_audio_fault(")
        ]
        self.assertGreaterEqual(
            audio_control.count("audio_capture_authorized(conn)"),
            2,
        )
        self.assertIn("bt_conn_unref(conn)", audio_control)

        notify_retry = transport[
            transport.index("static int notify_with_bounded_retry(") :
            transport.index("struct audio_tx_state {")
        ]
        retry_loop = notify_retry[notify_retry.index("for (uint8_t attempt") :]
        self.assertLess(
            retry_loop.index("audio_capture_authorized(conn)"),
            retry_loop.index("bt_gatt_notify("),
        )

        send_fragment = transport[
            transport.index("static int send_next_fragment(") :
            transport.index("K_THREAD_STACK_DEFINE(pusher_stack")
        ]
        self.assertLess(
            send_fragment.index("audio_capture_authorized(conn)"),
            send_fragment.index("bt_gatt_get_mtu(conn)"),
        )

        pusher = transport[
            transport.index("static void pusher(") :
            transport.index("int broadcast_audio_packets(")
        ]
        self.assertIn("audio_capture_authorized(conn)", pusher)
        self.assertNotIn("bt_gatt_is_subscribed(", pusher)

    def test_battery_smoother_executes_expected_fixed_point_vectors(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("host C compiler unavailable")
        harness = self.temporary / "battery_smoother_test.c"
        executable = self.temporary / "battery_smoother_test"
        harness.write_text(
            """
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include "battery_smoother.h"

int main(void)
{
    struct battery_smoother smoother;
    const uint8_t samples[] = {80, 100, 60, 60, 60, 255};
    const uint8_t expected[] = {80, 85, 79, 74, 71, 78};
    battery_smoother_reset(&smoother);
    for (size_t index = 0; index < sizeof(samples); ++index) {
        assert(battery_smoother_update(&smoother, samples[index]) == expected[index]);
    }
    battery_smoother_reset(&smoother);
    assert(battery_smoother_update(&smoother, 42) == 42);
    return 0;
}
""".lstrip(),
            encoding="utf-8",
        )
        subprocess.run(
            [
                compiler,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(self.source / "src"),
                str(self.source / "src" / "battery_smoother.c"),
                str(harness),
                "-o",
                str(executable),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run([str(executable)], check=True)

    def test_battery_divider_math_preserves_ratio_and_rejects_overflow(
        self,
    ) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("host C compiler unavailable")
        harness = self.temporary / "battery_math_test.c"
        executable = self.temporary / "battery_math_test"
        harness.write_text(
            r"""
#include <assert.h>
#include <errno.h>
#include <stddef.h>
#include <stdint.h>

#include "battery_math.h"

int main(void)
{
    uint16_t output = 0xaaaau;
    assert(battery_scale_divider_millivolts(
               1200u, 1037u, 510u, &output) == 0);
    assert(output == 3640u);
    assert(output != 3600u);

    output = 0xaaaau;
    assert(battery_scale_divider_millivolts(
               0u, 1037u, 510u, &output) == 0);
    assert(output == 0u);

    output = 0xaaaau;
    assert(battery_scale_divider_millivolts(
               1u, 1037u, 0u, &output) == -EINVAL);
    assert(output == 0xaaaau);
    assert(battery_scale_divider_millivolts(
               1u, 1037u, 510u, NULL) == -EINVAL);
    assert(battery_scale_divider_millivolts(
               UINT32_MAX, UINT32_MAX, UINT32_MAX, &output) ==
           -EOVERFLOW);
    assert(output == 0xaaaau);
    return 0;
}
""".lstrip(),
            encoding="utf-8",
        )
        subprocess.run(
            [
                compiler,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(self.source / "src"),
                str(self.source / "src" / "battery_math.c"),
                str(harness),
                "-o",
                str(executable),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            [str(executable)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_transport_fragment_helpers_execute_boundary_vectors_under_sanitizers(
        self,
    ) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("host C compiler unavailable")
        harness = self.temporary / "transport_safety_test.c"
        executable = self.temporary / "transport_safety_test"
        harness.write_text(
            r"""
#include <assert.h>
#include <errno.h>
#include <stddef.h>
#include <stdint.h>

#include "transport_safety.h"

static void assert_unchanged(
    const struct transport_fragment_state *expected,
    const struct transport_fragment_state *observed)
{
    assert(expected->offset == observed->offset);
    assert(expected->sequence == observed->sequence);
    assert(expected->fragment_index == observed->fragment_index);
}

int main(void)
{
    const struct transport_fragment_state initial = {
        .offset = 0u,
        .sequence = UINT16_MAX,
        .fragment_index = 0u,
    };
    size_t payload = 0xaaaau;
    assert(transport_fragment_plan(99u, 320u, &initial, &payload) ==
           -EMSGSIZE);
    assert(payload == 0xaaaau);
    assert(transport_fragment_plan(100u, 320u, &initial, &payload) == 0);
    assert(payload == 94u);
    assert(payload + TRANSPORT_AUDIO_HEADER_BYTES <=
           100u - TRANSPORT_ATT_NOTIFY_OVERHEAD_BYTES);
    assert(transport_fragment_plan(185u, 320u, &initial, &payload) == 0);
    assert(payload == 179u);

    const size_t expected_payloads[] = {94u, 94u, 94u, 38u};
    struct transport_fragment_state state = initial;
    for (size_t index = 0u;
         index < sizeof(expected_payloads) / sizeof(expected_payloads[0]);
         ++index) {
        assert(transport_fragment_plan(
                   100u, 320u, &state, &payload) == 0);
        assert(payload == expected_payloads[index]);
        assert(payload + TRANSPORT_AUDIO_HEADER_BYTES <=
               100u - TRANSPORT_ATT_NOTIFY_OVERHEAD_BYTES);
        struct transport_fragment_state next = {
            .offset = 0xaaaaaaaau,
            .sequence = 0xbbbbu,
            .fragment_index = 0xccu,
        };
        assert(transport_fragment_commit(
                   &state, payload, 0, &next) == 0);
        assert(next.offset == state.offset + payload);
        assert(next.sequence == (uint16_t)(state.sequence + 1u));
        assert(next.fragment_index ==
               (uint8_t)(state.fragment_index + 1u));
        if (index == 0u) {
            assert(next.sequence == 0u);
        }
        state = next;
    }
    assert(state.offset == 320u);
    assert(state.fragment_index == 4u);

    const struct transport_fragment_state current = {
        .offset = 29u,
        .sequence = 31u,
        .fragment_index = 3u,
    };
    const struct transport_fragment_state sentinel = {
        .offset = 0xaaaaaaaau,
        .sequence = 0xbbbbu,
        .fragment_index = 0xccu,
    };
    struct transport_fragment_state next = sentinel;
    assert(transport_fragment_commit(
               &current, 80u, -EIO, &next) == -EIO);
    assert_unchanged(&sentinel, &next);
    assert(transport_fragment_commit(
               &current, 80u, -EAGAIN, &next) == -EAGAIN);
    assert_unchanged(&sentinel, &next);
    assert(transport_fragment_commit(
               &current, 0u, 0, &next) == -ERANGE);
    assert_unchanged(&sentinel, &next);

    const struct transport_fragment_state offset_overflow = {
        .offset = UINT32_MAX,
        .sequence = 1u,
        .fragment_index = 1u,
    };
    assert(transport_fragment_commit(
               &offset_overflow, 1u, 0, &next) == -EOVERFLOW);
    assert_unchanged(&sentinel, &next);

    const struct transport_fragment_state index_overflow = {
        .offset = 0u,
        .sequence = 1u,
        .fragment_index = UINT8_MAX,
    };
    assert(transport_fragment_commit(
               &index_overflow, 1u, 0, &next) == -EOVERFLOW);
    assert_unchanged(&sentinel, &next);

    payload = 0xaaaau;
    assert(transport_fragment_plan(
               100u, 320u, NULL, &payload) == -EINVAL);
    assert(payload == 0xaaaau);
    assert(transport_fragment_plan(
               100u, 320u, &initial, NULL) == -EINVAL);
    const struct transport_fragment_state complete = {
        .offset = 320u,
        .sequence = 0u,
        .fragment_index = 4u,
    };
    assert(transport_fragment_plan(
               100u, 320u, &complete, &payload) == -ERANGE);
    assert(payload == 0xaaaau);
    return 0;
}
""".lstrip(),
            encoding="utf-8",
        )
        compile_command = [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(self.source / "src"),
            str(self.source / "src" / "transport_safety.c"),
            str(harness),
            "-o",
            str(executable),
        ]
        subprocess.run(
            compile_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            [str(executable)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        sanitizer_command = [
            *compile_command[:-2],
            "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer",
            "-o",
            str(executable),
        ]
        try:
            subprocess.run(
                sanitizer_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as exc:
            self.skipTest(
                "host compiler has no AddressSanitizer/UBSan support: "
                + exc.stderr.decode("utf-8", errors="replace")
            )
        subprocess.run(
            [str(executable)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


class LockedSourceTreeExportTests(unittest.TestCase):
    def test_export_uses_committed_tree_not_contaminated_worktree(self) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix="locked-tree-export-", dir=FIRMWARE_ROOT / ".build")
        )
        try:
            checkout = temporary / "checkout"
            source = checkout / "source"
            source.mkdir(parents=True)
            (source / ".gitignore").write_text("ignored.bin\n", encoding="utf-8")
            tracked = source / "tracked.txt"
            tracked.write_text("committed\n", encoding="utf-8")
            executable = source / "tool.sh"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            (source / "tracked-link").symlink_to("tracked.txt")
            subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
            subprocess.run(["git", "add", "."], cwd=checkout, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Anticipy Test",
                    "-c",
                    "user.email=test@invalid.example",
                    "commit",
                    "--quiet",
                    "-m",
                    "fixture",
                ],
                cwd=checkout,
                check=True,
            )

            tracked.write_text("dirty worktree\n", encoding="utf-8")
            (source / "ignored.bin").write_bytes(b"ignored contamination")
            (source / "untracked.txt").write_text("untracked\n", encoding="utf-8")

            destination = temporary / "export"
            destination.mkdir()
            export_locked_source_tree(checkout, "source", destination)

            self.assertEqual((destination / "tracked.txt").read_text(), "committed\n")
            self.assertFalse((destination / "ignored.bin").exists())
            self.assertFalse((destination / "untracked.txt").exists())
            self.assertTrue((destination / "tool.sh").stat().st_mode & 0o100)
            self.assertTrue((destination / "tracked-link").is_symlink())
            self.assertEqual((destination / "tracked-link").readlink(), Path("tracked.txt"))
        finally:
            shutil.rmtree(temporary, ignore_errors=True)


@unittest.skipUnless(
    UPSTREAM_CHECKOUT.is_dir(),
    "locked upstream checkout absent; full-tree receipt test requires fetch_upstream.py",
)
class FullMaterializationReceiptTests(unittest.TestCase):
    def test_0002_alone_materializes_the_locked_final_tree_and_receipt(self) -> None:
        (FIRMWARE_ROOT / ".build").mkdir(exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix="replacement-full-tree-", dir=FIRMWARE_ROOT / ".build")
        )
        try:
            source = temporary / "source"
            receipt = materialize(UPSTREAM_CHECKOUT, source)
            receipt_path = source / SOURCE_RECEIPT_NAME
            on_disk = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk, receipt)
            self.assertEqual(
                on_disk["patch"]["path"],
                "replacement/patches/0002-anticipy-source-safety.patch",
            )
            self.assertFalse(on_disk["artifact_built"])
            self.assertFalse(on_disk["flash_performed"])
            self.assertFalse(on_disk["physical_hardware_verified"])
            observed_sha256 = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            replacement = json.loads(REPLACEMENT_LOCK.read_text(encoding="utf-8"))
            self.assertEqual(
                observed_sha256,
                replacement["materialized_source"]["source_receipt_sha256"],
            )
            self.assertEqual(
                content_tree_sha256(source),
                replacement["materialized_source"]["content_tree_sha256"],
            )
            self.assertEqual(
                set(on_disk["materialized_source"]["critical_file_sha256"]),
                set(replacement["materialized_source"]["critical_file_sha256"]),
            )
            for absent in (
                "CMakePresets.json",
                "build.sh",
                "client.py",
                "overlay/xiao_ble_sense_devkitv1-spisd.overlay",
                "overlay/xiao_ble_sense_devkitv1.overlay",
                "prj_xiao_ble_sense_devkitv1-spisd.conf",
                "prj_xiao_ble_sense_devkitv1.conf",
                "src/button.c",
                "src/button.h",
                "src/nfc.c",
                "src/nfc.h",
                "src/sdcard.c",
                "src/sdcard.h",
                "src/speaker.c",
                "src/speaker.h",
                "src/storage.c",
                "src/storage.h",
            ):
                self.assertFalse((source / absent).exists(), absent)

            main = (source / "src" / "main.c").read_text(encoding="utf-8")
            self.assertLess(main.index("led_start()"), main.index("codec_start()"))
            self.assertLess(main.index("codec_start()"), main.index("mic_init()"))
            self.assertLess(main.index("mic_init()"), main.index("transport_start()"))
            self.assertIn("mic_emergency_power_off()", main)
            self.assertIn("k_panic()", main)

            mic = (source / "src" / "mic.c").read_text(encoding="utf-8")
            self.assertIn("IRQ_CONNECT(", mic)
            self.assertIn("nrfx_isr, nrfx_pdm_irq_handler", mic)
            self.assertNotIn("IRQ_DIRECT_CONNECT", mic)
            self.assertIn("k_sem_take(&pdm_stopped", mic)
            self.assertIn("nrfx_pdm_enable_check()", mic)
            self.assertLess(
                mic.index("k_sem_take(&pdm_stopped"),
                mic.index("memset(buffer_0", mic.index("k_sem_take(&pdm_stopped")),
            )
            self.assertNotIn("pdm_fault_work", mic)

            codec = (source / "src" / "codec.c").read_text(encoding="utf-8")
            self.assertIn("OPUS_RESET_STATE", codec)
            self.assertIn("if (output_size < 0)", codec)
            self.assertIn("error_callback(-EIO)", codec)

            battery = (
                source / "src" / "lib" / "battery" / "battery.c"
            ).read_text(encoding="utf-8")
            self.assertIn('#include "../../battery_math.h"', battery)
            self.assertIn("battery_scale_divider_millivolts(", battery)
            self.assertNotIn(
                "(divider_high_kohm + divider_low_kohm) / "
                "divider_low_kohm",
                battery,
            )

            readme = (source / "README.rst").read_text(encoding="utf-8")
            self.assertIn("not production firmware", readme)
            self.assertIn("first nearby central", readme)
            self.assertNotIn("Flashing the Firmware", readme)
        finally:
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
