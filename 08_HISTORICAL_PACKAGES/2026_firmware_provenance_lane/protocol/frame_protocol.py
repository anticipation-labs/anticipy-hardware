"""Fail-closed reassembly for the pinned Omi v2.0.1-era BLE audio packets.

This is a reference/fixture implementation. Production iOS code must implement
the same contract natively and validate each emitted payload as an Opus packet.
"""

from __future__ import annotations

from dataclasses import dataclass


HEADER_BYTES = 3
SEQUENCE_MODULUS = 1 << 16
DEFAULT_MAX_FRAME_BYTES = 320
DEFAULT_MAX_FRAGMENTS = 4


@dataclass
class ReassemblyStats:
    frames_emitted: int = 0
    dropped_frames: int = 0
    duplicate_packets: int = 0
    malformed_packets: int = 0
    sequence_discontinuities: int = 0
    out_of_order_fragments: int = 0
    orphan_fragments: int = 0
    oversized_frames: int = 0


def packet(sequence: int, fragment: int, payload: bytes) -> bytes:
    """Build one legacy notification for fixtures and cross-client tests."""
    if not 0 <= sequence < SEQUENCE_MODULUS:
        raise ValueError("sequence must fit uint16")
    if not 0 <= fragment <= 0xFF:
        raise ValueError("fragment must fit uint8")
    if not payload:
        raise ValueError("payload must not be empty")
    return sequence.to_bytes(2, "little") + bytes((fragment,)) + payload


class FrameReassembler:
    """Reassemble a notification stream without joining across uncertainty.

    The legacy firmware has no frame length or final-fragment flag. A frame is
    emitted when the next fragment-zero packet arrives or when ``finish`` is
    called intentionally at stream shutdown. Any discontinuity drops the whole
    pending frame.
    """

    def __init__(
        self,
        *,
        max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES,
        max_fragments: int = DEFAULT_MAX_FRAGMENTS,
    ) -> None:
        if max_frame_bytes <= 0:
            raise ValueError("max_frame_bytes must be positive")
        if not 1 <= max_fragments <= 0x100:
            raise ValueError("max_fragments must be between 1 and 256")
        self.max_frame_bytes = max_frame_bytes
        self.max_fragments = max_fragments
        self.stats = ReassemblyStats()
        self._pending: bytearray | None = None
        self._expected_fragment = 0
        self._last_sequence: int | None = None
        self._last_packet: bytes | None = None

    def feed(self, notification: bytes) -> list[bytes]:
        """Consume one BLE notification and return zero or one complete frames."""
        raw = bytes(notification)
        if len(raw) <= HEADER_BYTES:
            self.stats.malformed_packets += 1
            return []

        sequence = int.from_bytes(raw[0:2], "little")
        fragment = raw[2]
        payload = raw[HEADER_BYTES:]

        if self._last_packet == raw:
            self.stats.duplicate_packets += 1
            return []

        if fragment >= self.max_fragments:
            self.stats.out_of_order_fragments += 1
            self._drop_pending()
            self._remember(sequence, raw)
            return []

        if self._last_sequence is not None:
            expected_sequence = (self._last_sequence + 1) % SEQUENCE_MODULUS
            if sequence != expected_sequence:
                conflicting_duplicate = sequence == self._last_sequence
                self.stats.sequence_discontinuities += 1
                self._drop_pending()
                self._remember(sequence, raw)
                if fragment == 0 and not conflicting_duplicate:
                    self._start(payload)
                elif fragment != 0:
                    self.stats.orphan_fragments += 1
                return []

        emitted: list[bytes] = []
        if fragment == 0:
            previous = self._emit_pending()
            if previous is not None:
                emitted.append(previous)
            self._start(payload)
        elif self._pending is None:
            self.stats.orphan_fragments += 1
        elif fragment != self._expected_fragment:
            self.stats.out_of_order_fragments += 1
            self._drop_pending()
        elif len(self._pending) + len(payload) > self.max_frame_bytes:
            self.stats.oversized_frames += 1
            self._drop_pending()
        else:
            self._pending.extend(payload)
            self._expected_fragment += 1

        self._remember(sequence, raw)
        return emitted

    def finish(self) -> list[bytes]:
        """Flush the last valid pending frame at an intentional stream boundary."""
        frame = self._emit_pending()
        self._last_sequence = None
        self._last_packet = None
        return [] if frame is None else [frame]

    def reset(self) -> None:
        """Drop pending bytes and all sequence state without emitting audio."""
        self._drop_pending()
        self._last_sequence = None
        self._last_packet = None

    def _start(self, payload: bytes) -> None:
        if len(payload) > self.max_frame_bytes:
            self.stats.oversized_frames += 1
            self._pending = None
            self._expected_fragment = 0
            return
        self._pending = bytearray(payload)
        self._expected_fragment = 1

    def _emit_pending(self) -> bytes | None:
        if self._pending is None:
            return None
        frame = bytes(self._pending)
        self._pending = None
        self._expected_fragment = 0
        if not frame:
            return None
        self.stats.frames_emitted += 1
        return frame

    def _drop_pending(self) -> None:
        if self._pending is not None:
            self.stats.dropped_frames += 1
        self._pending = None
        self._expected_fragment = 0

    def _remember(self, sequence: int, raw: bytes) -> None:
        self._last_sequence = sequence
        self._last_packet = raw
