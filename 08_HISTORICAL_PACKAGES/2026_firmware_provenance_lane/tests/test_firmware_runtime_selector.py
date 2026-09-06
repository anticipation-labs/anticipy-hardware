from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTOR = REPO_ROOT / "firmware" / "scripts" / "select_sbom_python.sh"
CHECK = REPO_ROOT / "check.sh"
BASH = shutil.which("bash")


class FirmwareRuntimeSelectorTests(unittest.TestCase):
    def run_selector(
        self,
        *,
        override: str | None,
        path: str | None = None,
        environment_updates: dict[str, str] | None = None,
    ):
        environment = os.environ.copy()
        if override is None:
            environment.pop("ANTICIPY_FIRMWARE_PYTHON", None)
        else:
            environment["ANTICIPY_FIRMWARE_PYTHON"] = override
        if path is not None:
            environment["PATH"] = path
        if environment_updates is not None:
            environment.update(environment_updates)
        return subprocess.run(
            [BASH, str(SELECTOR)],
            cwd=REPO_ROOT,
            env=environment,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @unittest.skipIf(BASH is None, "bash is required by the repository check")
    def test_accepts_exact_locked_runtime_override_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="anticipy firmware runtime ") as root:
            candidate = Path(root) / "pinned python"
            candidate.symlink_to(sys.executable)
            result = self.run_selector(override=str(candidate))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(candidate))
        self.assertEqual(result.stderr, "")

    @unittest.skipIf(BASH is None, "bash is required by the repository check")
    def test_rejects_override_that_does_not_prove_runtime_lock(self) -> None:
        result = self.run_selector(override="/usr/bin/true")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("does not satisfy", result.stderr)

    @unittest.skipIf(BASH is None, "bash is required by the repository check")
    def test_ignores_ambient_python_module_injection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="anticipy-firmware-shadow-") as root:
            Path(root, "jsonschema.py").write_text(
                'raise RuntimeError("ambient validator module was imported")\n',
                encoding="utf-8",
            )
            hostile_environment = {
                "PYTHONPATH": root,
                "PYTHONNOUSERSITE": "0",
                "PYTHONOPTIMIZE": "2",
            }
            unisolated_environment = os.environ.copy()
            unisolated_environment.update(hostile_environment)
            poisoned = subprocess.run(
                [sys.executable, "-s", "-c", "import jsonschema"],
                env=unisolated_environment,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = self.run_selector(
                override=sys.executable,
                environment_updates=hostile_environment,
            )

        self.assertNotEqual(poisoned.returncode, 0)
        self.assertIn("ambient validator module was imported", poisoned.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), sys.executable)

    @unittest.skipIf(BASH is None, "bash is required by the repository check")
    def test_discovers_exact_python310_from_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="anticipy-firmware-path-") as root:
            candidate = Path(root) / "python3.10"
            candidate.symlink_to(sys.executable)
            result = self.run_selector(override=None, path=root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(candidate))

    @unittest.skipIf(BASH is None, "bash is required by the repository check")
    def test_fails_closed_when_no_locked_runtime_is_available(self) -> None:
        with tempfile.TemporaryDirectory(prefix="anticipy-firmware-empty-path-") as root:
            result = self.run_selector(override=None, path=root)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("No Python satisfies", result.stderr)

    def test_master_check_routes_every_firmware_python_step_to_selector(self) -> None:
        check = CHECK.read_text(encoding="utf-8")
        firmware_section = check.split(
            'echo "== firmware evidence contract =="', 1
        )[1].split('echo "== web/orchestrator contract =="', 1)[0]

        self.assertIn(
            'firmware_python="$(bash firmware/scripts/select_sbom_python.sh)"',
            check,
        )
        self.assertIn(
            'PYTHONPATH= PYTHONNOUSERSITE=1 "$firmware_python" -E -s "$@"',
            check,
        )
        self.assertNotIn('"$core_python"', firmware_section)
        self.assertEqual(firmware_section.count("run_firmware_python"), 3)


if __name__ == "__main__":
    unittest.main()
