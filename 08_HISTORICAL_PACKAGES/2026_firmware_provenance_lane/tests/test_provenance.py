from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIRMWARE_ROOT / "scripts"))

from uf2 import UF2Error, inspect_uf2  # noqa: E402


class ProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = json.loads(
            (FIRMWARE_ROOT / "upstream.lock.json").read_text(encoding="utf-8")
        )
        self.manifest = json.loads(
            (FIRMWARE_ROOT / "quarantine" / "manifest.json").read_text(encoding="utf-8")
        )

    def test_upstream_lock_uses_immutable_commit_and_tree(self) -> None:
        self.assertRegex(self.lock["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(self.lock["source_tree_git_oid"], r"^[0-9a-f]{40}$")
        self.assertEqual(self.lock["tag"], "v2.0.1-Omi")
        self.assertEqual(self.lock["source_path"], "Friend/firmware/firmware_v1.0")
        self.assertNotIn("main", self.lock["commit"])

    def test_vendored_license_matches_locked_git_blob(self) -> None:
        license_bytes = (FIRMWARE_ROOT / "LICENSES" / "BasedHardware-Omi-MIT.txt").read_bytes()
        source_license = license_bytes.split(b"\nSource:", 1)[0]
        git_object = f"blob {len(source_license)}\0".encode() + source_license
        actual_oid = hashlib.sha1(git_object).hexdigest()
        self.assertEqual(actual_oid, self.lock["license_blob_git_oid"])

    def test_quarantine_bytes_and_structure_match_manifest(self) -> None:
        artifact = FIRMWARE_ROOT / "quarantine" / self.manifest["file"]
        observed = inspect_uf2(artifact)
        self.assertEqual(observed["sha256"], self.manifest["sha256"])
        self.assertEqual(observed["bytes"], self.manifest["bytes"])
        self.assertEqual(observed["blocks"], self.manifest["uf2"]["blocks"])
        self.assertEqual(observed["family_ids"], [self.manifest["uf2"]["family_id"]])
        self.assertEqual(observed["address_start"], self.manifest["uf2"]["address_start"])
        self.assertEqual(
            observed["address_end_exclusive"],
            self.manifest["uf2"]["address_end_exclusive"],
        )

    def test_quarantine_is_explicitly_not_official_release(self) -> None:
        official = self.lock["official_release_asset"]
        self.assertEqual(self.manifest["classification"], "UNVERIFIED_DO_NOT_FLASH")
        self.assertNotEqual(self.manifest["sha256"], official["sha256"])
        self.assertFalse(self.manifest["official_release_comparison"]["identical"])

    def test_uf2_inspector_rejects_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "truncated.invalid.uf2"
            path.write_bytes(b"not a block")
            with self.assertRaises(UF2Error):
                inspect_uf2(path)


if __name__ == "__main__":
    unittest.main()
