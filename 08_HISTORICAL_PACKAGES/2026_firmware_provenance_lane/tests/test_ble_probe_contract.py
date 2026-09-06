from __future__ import annotations

import unittest
from pathlib import Path


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]


class BLEProbeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.swift = (FIRMWARE_ROOT / "scripts" / "omi_ble_probe.swift").read_text(
            encoding="utf-8"
        )
        cls.html = (FIRMWARE_ROOT / "scripts" / "omi_ble_probe.html").read_text(
            encoding="utf-8"
        )

    def test_native_probe_requires_an_explicit_start_action(self) -> None:
        launch = self.swift.split("func applicationDidFinishLaunching", 1)[1].split(
            "@objc private func startProbe", 1
        )[0]
        start = self.swift.split("@objc private func startProbe", 1)[1]
        self.assertNotIn("OmiBLEProbe(captureSeconds:", launch)
        self.assertIn("OmiBLEProbe(captureSeconds:", start)
        self.assertIn("awaiting_explicit_start=true", launch)

    def test_native_success_flushes_and_requires_real_audio(self) -> None:
        stop = self.swift.split("private func stop(reason:", 1)[1].split(
            "private func finish", 1
        )[0]
        self.assertLess(stop.index("metrics.flush()"), stop.index("metrics.validFrames == 0"))
        self.assertIn('finalReason = "no_audio_notifications"', stop)
        self.assertIn('finalReason = "no_valid_opus_frames"', stop)

    def test_native_result_preserves_present_optional_values(self) -> None:
        self.assertIn('"codec": codec.map { $0 as Any } ?? NSNull()', self.swift)
        self.assertIn(
            '"captureSecondsActual": elapsed.map { $0 as Any } ?? NSNull()', self.swift
        )
        self.assertNotIn('output["codec"] is Optional<Int>', self.swift)

    def test_web_success_requires_notifications_and_valid_opus(self) -> None:
        self.assertIn("if (notificationCount === 0) throw new Error('no_audio_notifications')", self.html)
        self.assertIn("if (frames.length === 0) throw new Error('no_valid_opus_frames')", self.html)
        self.assertLess(
            self.html.index("emitFrame();\n    if (notificationCount === 0)"),
            self.html.index("window.__omiProbeState = 'complete'"),
        )
        self.assertIn("button.textContent = 'Reload this page to retry'", self.html)
        self.assertNotIn("button.disabled = false", self.html)


if __name__ == "__main__":
    unittest.main()
