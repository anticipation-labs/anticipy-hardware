from __future__ import annotations

import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIRMWARE_ROOT))

from protocol.frame_protocol import FrameReassembler, packet  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures" / "audio_packet_streams.json"


class PacketFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))

    def test_all_packet_stream_fixtures(self) -> None:
        self.assertEqual(self.fixture["schema"], 1)
        names: set[str] = set()
        for case in self.fixture["cases"]:
            with self.subTest(case=case["name"]):
                names.add(case["name"])
                reassembler = FrameReassembler()
                frames: list[bytes] = []
                for encoded in case["packets_hex"]:
                    frames.extend(reassembler.feed(bytes.fromhex(encoded)))
                if case.get("finish"):
                    frames.extend(reassembler.finish())
                self.assertEqual([frame.hex() for frame in frames], case["frames_hex"])

                actual_stats = asdict(reassembler.stats)
                for key, expected in case.get("stats", {}).items():
                    self.assertEqual(actual_stats[key], expected, key)

        required = {
            "sequence_gap_drops_pending_frame",
            "exact_duplicate_is_ignored",
            "out_of_order_fragment_drops_pending_frame",
            "uint16_sequence_wrap_is_contiguous",
            "final_flush_preserves_last_frame",
        }
        self.assertTrue(required.issubset(names))

    def test_frame_larger_than_firmware_buffer_is_dropped(self) -> None:
        reassembler = FrameReassembler(max_frame_bytes=320)
        self.assertEqual(reassembler.feed(packet(1, 0, b"a" * 200)), [])
        self.assertEqual(reassembler.feed(packet(2, 1, b"b" * 121)), [])
        self.assertEqual(reassembler.finish(), [])
        self.assertEqual(reassembler.stats.oversized_frames, 1)
        self.assertEqual(reassembler.stats.dropped_frames, 1)

    def test_fragment_index_beyond_firmware_max_is_dropped(self) -> None:
        reassembler = FrameReassembler(max_fragments=4)
        reassembler.feed(packet(7, 0, b"a"))
        self.assertEqual(reassembler.feed(packet(8, 4, b"b")), [])
        self.assertEqual(reassembler.finish(), [])
        self.assertEqual(reassembler.stats.out_of_order_fragments, 1)
        self.assertEqual(reassembler.stats.dropped_frames, 1)

    def test_reset_never_emits_pending_audio(self) -> None:
        reassembler = FrameReassembler()
        reassembler.feed(packet(7, 0, b"sensitive"))
        reassembler.reset()
        self.assertEqual(reassembler.finish(), [])
        self.assertEqual(reassembler.stats.dropped_frames, 1)

    def test_packet_builder_validates_fields(self) -> None:
        with self.assertRaises(ValueError):
            packet(-1, 0, b"x")
        with self.assertRaises(ValueError):
            packet(0, 256, b"x")
        with self.assertRaises(ValueError):
            packet(0, 0, b"")


if __name__ == "__main__":
    unittest.main()
