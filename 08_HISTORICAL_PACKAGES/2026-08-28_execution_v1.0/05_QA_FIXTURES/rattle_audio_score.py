#!/usr/bin/env python3
"""Compare one pause-only DUT recording with qualified golden recordings.

The fixture's marker output is HIGH during each quiet pause. Export only those
marked pause segments to PCM WAV before using this program. Keep microphone,
contact-sensor position, gain, sample rate and cassette index unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import wave

import numpy as np


def load_pcm_wav(path: Path) -> tuple[np.ndarray, int, float]:
    with wave.open(str(path), "rb") as wav:
        if wav.getcomptype() != "NONE":
            raise ValueError(f"{path}: compressed WAV is unsupported")
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        frames = wav.getnframes()
        raw = wav.readframes(frames)

    if channels < 1 or rate < 8000 or frames < rate // 5:
        raise ValueError(f"{path}: need at least 0.2 s of audio at >=8 kHz")

    if width == 1:
        values = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    elif width == 2:
        values = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        integers = (
            b[:, 0].astype(np.int32)
            | (b[:, 1].astype(np.int32) << 8)
            | (b[:, 2].astype(np.int32) << 16)
        )
        integers = np.where(integers & 0x800000, integers - 0x1000000, integers)
        values = integers.astype(np.float64) / 8388608.0
    elif width == 4:
        values = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"{path}: unsupported {width * 8}-bit PCM")

    values = values.reshape(-1, channels).mean(axis=1)
    peak = float(np.max(np.abs(values)))
    if peak >= 0.999:
        raise ValueError(f"{path}: recording clips; lower the fixed input gain and repeat")
    values -= float(np.mean(values))
    return values, rate, peak


def impulse_score_db(path: Path, window_ms: float) -> dict:
    signal, rate, peak = load_pcm_wav(path)
    # First difference suppresses slow room/motor rumble and emphasizes clicks.
    differentiated = np.diff(signal, prepend=signal[0])
    window = max(2, int(round(rate * window_ms / 1000.0)))
    energy = np.convolve(differentiated * differentiated, np.ones(window) / window, mode="valid")
    trim = int(round(rate * 0.05))
    if len(energy) > 2 * trim:
        energy = energy[trim:-trim]
    max_rms = math.sqrt(max(float(np.max(energy)), 1e-20))
    p999_rms = math.sqrt(max(float(np.percentile(energy, 99.9)), 1e-20))
    return {
        "file": str(path),
        "sample_rate_hz": rate,
        "duration_s": round(len(signal) / rate, 4),
        "pcm_peak": round(peak, 6),
        "max_impulse_dbfs": round(20.0 * math.log10(max_rms), 3),
        "p99_9_impulse_dbfs": round(20.0 * math.log10(p999_rms), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", action="append", required=True, type=Path,
                        help="qualified pause-only golden WAV; repeat at least three times")
    parser.add_argument("--dut", required=True, type=Path, help="pause-only DUT WAV")
    parser.add_argument("--threshold-db", type=float, default=6.0,
                        help="reject above loudest golden plus this margin (default: 6 dB)")
    parser.add_argument("--window-ms", type=float, default=5.0,
                        help="short impulse RMS window (default: 5 ms)")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    if len(args.golden) < 3:
        parser.error("provide at least three qualified golden WAV recordings")
    if not 0.5 <= args.window_ms <= 50.0:
        parser.error("--window-ms must be between 0.5 and 50")
    if not 0.0 <= args.threshold_db <= 30.0:
        parser.error("--threshold-db must be between 0 and 30")

    try:
        golden = [impulse_score_db(p, args.window_ms) for p in args.golden]
        dut = impulse_score_db(args.dut, args.window_ms)
    except (OSError, ValueError, wave.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    golden_scores = [row["max_impulse_dbfs"] for row in golden]
    envelope = max(golden_scores)
    limit = envelope + args.threshold_db
    delta = dut["max_impulse_dbfs"] - envelope
    result = "PASS" if dut["max_impulse_dbfs"] <= limit else "FAIL"
    report = {
        "result": result,
        "method": "maximum 5-ms first-difference RMS in pause-only PCM WAV",
        "window_ms": args.window_ms,
        "threshold_above_loudest_golden_db": args.threshold_db,
        "golden_envelope_dbfs": round(envelope, 3),
        "dut_limit_dbfs": round(limit, 3),
        "dut_delta_above_envelope_db": round(delta, 3),
        "golden": golden,
        "dut": dut,
        "scope": (
            "Comparative rattle screening only; this is valid only after dummy, golden, "
            "seeded-challenge and repeatability qualification at unchanged gain and placement."
        ),
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
