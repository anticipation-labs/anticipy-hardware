"""Executable host-side contract for the legacy pendant audio transport."""

from .frame_protocol import FrameReassembler, ReassemblyStats, packet

__all__ = ["FrameReassembler", "ReassemblyStats", "packet"]
